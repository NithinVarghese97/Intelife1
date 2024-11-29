import pandas as pd
import numpy as np
from ast import literal_eval
from scipy.spatial.distance import cosine
import tiktoken
from openai import OpenAI
import os
import re
from dotenv import load_dotenv
from tqdm import tqdm
from typing import List, Tuple, Dict, Any


load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)


def split_into_many(tokenizer, text, max_tokens):
    sentences = text.split('. ')
    n_tokens = [len(tokenizer.encode(" " + sentence)) for sentence in sentences]
    chunks = []
    tokens_so_far = 0
    chunk = []
    for sentence, token in zip(sentences, n_tokens):
        if tokens_so_far + token > max_tokens:
            chunks.append(". ".join(chunk) + ".")
            chunk = []
            tokens_so_far = 0
        if token > max_tokens:
            continue
        chunk.append(sentence)
        tokens_so_far += token + 1
    if chunk:
        chunks.append(". ".join(chunk) + ".")
    return chunks


def get_embedding(text, model="text-embedding-ada-002"):
    text = text.replace("\n", " ")
    return client.embeddings.create(input=[text], model=model).data[0].embedding


def create_context(input, df, max_len=1800, size="ada"):
    q_embeddings = get_embedding(input)
    df["distances"] = df["embeddings"].apply(lambda x: cosine(q_embeddings, x))
    returns = []
    cur_len = 0
    for i, row in df.sort_values('distances', ascending=True).iterrows():
        cur_len += row['n_tokens'] + 4
        if cur_len > max_len:
            break
        returns.append(row["text"])
    return "\n\n###\n\n".join(returns)


def get_refinement_criteria() -> str:
    return """Please evaluate the translation based on the following criteria:
    1. Clarity: Is the easy-read translation clear and really simple to understand?
    2. Accuracy: Does it maintain the original meaning while being simpler?
    3. Readability: Is it structured in a way that's easy to follow?
    4. Consistency: Is the simplification level consistent throughout?
    5. Length: Easy read translation must be between 1 to 2 sentences only. Is the reuslting paragraph short?

    For each criterion, provide:
    - A score (1-5)
    - Specific issues identified
    - Suggested improvements

    Then, provide an improved version of the translation that addresses these issues."""


def refine_translation(client: OpenAI, current_text: str, original_input: str, context: str, 
                        model: str = "gpt-4-turbo") -> Tuple[str, Dict[str, Any]]:
    """Refine the given translation based on evaluation criteria."""
    refinement_prompt = f"""Original Text: {original_input}

    Current Translation:
    {current_text}

    Context from Similar Texts:
    {context}

    {get_refinement_criteria()}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in converting text to easy-read format while maintaining accuracy and clarity."},
                {"role": "user", "content": refinement_prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )
        
        feedback = response.choices[0].message.content
        improved_text = feedback.split("improved version")[-1].strip()
        
        return improved_text, {"full_feedback": feedback}
    
    except Exception as e:
        print(f"Error in refinement: {str(e)}")
        return current_text, {"error": str(e)}


def remove_newlines(serie):
    serie = serie.str.replace('\n', ' ')
    serie = serie.str.replace('\\n', ' ')
    serie = serie.str.replace('  ', ' ')
    serie = serie.str.replace('  ', ' ')
    return serie


def create_df():
    texts = []
    for file in os.listdir("app/text/"):
        with open("app/text/" + file, "r", encoding="UTF-8") as f:
            text = f.read()
            texts.append((file[11:-4].replace('-',' ').replace('_', ' ').replace('#update',''), text))
    
    df = pd.DataFrame(texts, columns=['fname', 'text'])
    df['text'] = df.fname + ". " + remove_newlines(df.text)
    
    if not os.path.exists("processed"):
        os.mkdir("processed")
    
    df.to_csv('processed/scraped.csv')
    return df


def convert_string_to_array(embedding_string):
    """Convert string representation of embedding to numpy array."""
    try:
        # Remove any trailing commas and cleanup the string
        clean_string = embedding_string.strip('[]').strip()
        if clean_string.endswith(','):
            clean_string = clean_string[:-1]
        # Convert to list of floats
        return np.array([float(x.strip()) for x in clean_string.split(',')])
    except Exception as e:
        print(f"Error converting embedding: {e}")
        return np.array([])


def prepare_embeddings_df():
    """Prepare and return DataFrame with embeddings."""
    if os.path.exists('embeddings.csv'):
        df = pd.read_csv('embeddings.csv', index_col=0)
        if 'embeddings' in df.columns:
            # Safely convert string embeddings to numpy arrays
            df['embeddings'] = df['embeddings'].apply(convert_string_to_array)
        return df
    
    # If embeddings.csv doesn't exist, create it
    tokenizer = tiktoken.get_encoding("cl100k_base")
    df = create_df()
    df.columns = ['title', 'text']
    
    # Process text and create embeddings
    df['n_tokens'] = df['text'].apply(lambda x: len(tokenizer.encode(x)))
    max_tokens = 1000
    
    shortened = []
    for row in df.iterrows():
        if row[1]['text'] is None:
            continue
        if row[1]['n_tokens'] > max_tokens:
            shortened += split_into_many(tokenizer, row[1]['text'], max_tokens)
        else:
            shortened.append(row[1]['text'])
    
    df = pd.DataFrame(shortened, columns=['text'])
    df['n_tokens'] = df.text.apply(lambda x: len(tokenizer.encode(x)))
    df['embeddings'] = df.text.apply(lambda x: get_embedding(x))
    
    # Save embeddings as JSON strings to preserve format
    df.to_csv('embeddings.csv')
    return df


def iterative_translation(input_text: str, n_iterations: int = 3, 
                         model: str = "gpt-4-turbo") -> List[Tuple[str, Dict[str, Any]]]:
    # Prepare embeddings DataFrame
    df = prepare_embeddings_df() if not os.path.exists('embeddings.csv') else pd.read_csv('embeddings.csv', index_col=0)
    if 'embeddings' in df.columns:
        df['embeddings'] = df['embeddings'].apply(literal_eval).apply(np.array)
    
    # Get context for the translation
    context = create_context(input_text, df)

    input_text = "User input: " + input_text + "\nContext: {context}"
    
    # Initial translation
    system_prompt = f"You are a translator, your role is to translate the user input text into easy read format based on BOTH the user input and the context."
    
    try:
        response = client.chat.completions.create(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": input_text}
            ],
            temperature=0,
            max_tokens=2000,
            model=model
        )
        current_text = response.choices[0].message.content
    except Exception as e:
        print(f"Error in initial translation: {str(e)}")
        return []
    
    results = [(current_text, {"stage": "initial"})]
    
    # Refinement loop
    for i in tqdm(range(n_iterations), desc="Refining translation"):
        try:
            refined_text, feedback = refine_translation(
                client=client,
                current_text=current_text,
                original_input=input_text,
                context=context,
                model=model
            )
            
            results.append((refined_text, {
                "stage": f"refinement_{i+1}",
                "feedback": feedback
            }))
            current_text = refined_text
            
        except Exception as e:
            print(f"Error in iteration {i+1}: {str(e)}")
            break
    
    return results


def save_refinement_history(results: List[Tuple[str, Dict[str, Any]]], filename: str = "translation_history.txt"):
    """Save the refinement history to a file."""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== Translation Refinement History ===\n\n")
        for i, (text, metadata) in enumerate(results):
            f.write(f"\n--- Stage: {metadata['stage']} ---\n")
            f.write(text + "\n")
            if i > 0 and "feedback" in metadata:
                f.write("\nFeedback from previous version:\n")
                f.write(metadata["feedback"]["full_feedback"] + "\n")
            f.write("\n" + "="*50 + "\n")


def extract_translation(input_list):
    improved_versions = []
    
    for item in input_list:
        feedback = item[1].get('feedback', {})
        improved_version = feedback.get('full_feedback', '')
        
        match = re.search(r"### Improved Version of the Translation:\n\n\"([^\"]+)\"", improved_version)
        
        if match:
            improved_versions.append(match.group(1))
    
    return improved_versions


def translate(input_text):
    # Run iterative translation
    results = iterative_translation(input_text, n_iterations=3)
    opt = extract_translation(results)
    
    # Save results
    save_refinement_history(results)

    return opt
