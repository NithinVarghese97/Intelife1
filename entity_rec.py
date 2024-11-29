from openai import OpenAI
import os
from dotenv import load_dotenv
from tqdm import tqdm
from typing import List, Tuple, Dict, Any, Optional


load_dotenv()
api_key = os.getenv('API_KEY')
client = OpenAI(api_key=api_key)


def get_refinement_criteria() -> str:
    return """Please evaluate the prompt based on the following criteria:
    1. Clarity: Is the prompt clear and really simple to understand?
    2. Accuracy: Does it maintain the original meaning while being simpler?
    3. Geometry: Is the prompt actually describing an image?
    4. Simplicity: To make the generated image structually simple, the prompt must not include many details.
    5. Constraints: The image must not contain any text. Does the prompt follow the constraint?

    For each criterion, provide:
    - A score (1-5)
    - Specific issues identified
    - Suggested improvements

    Then, provide an improved version of the translation that addresses these issues."""


def refine_translation(client: OpenAI, current_text: str, original_input: str, 
                        model: str = "gpt-4-turbo") -> Tuple[str, Dict[str, Any]]:
    """Refine the given prompt based on evaluation criteria."""
    refinement_prompt = f"""Original Text: {original_input}

    Current Translation:
    {current_text}

    {get_refinement_criteria()}"""

    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are an expert in converting plain text to clear and concise prompts for diffusion model use."},
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


def iterative_translation(input_text: str, n_iterations: int = 3, 
                         model: str = "gpt-4-turbo") -> List[Tuple[str, Dict[str, Any]]]:
    
    system_prompt = f"You are an expert in converting plain text to clear and concise prompts for diffusion model use."
    
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


def save_refinement_history(results: List[Tuple[str, Dict[str, Any]]], filename: str = "translation_history.txt") -> Optional[str]:
    last_quoted_line = None
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("=== Translation Refinement History ===\n\n")
        for i, (text, metadata) in enumerate(results):
            f.write(f"\n--- Stage: {metadata['stage']} ---\n")
            
            # Check each line in the text for quotes
            for line in text.split('\n'):
                line = line.strip()
                if line.startswith('"') and line.endswith('"'):
                    last_quoted_line = line
            
            f.write(text + "\n")
            
            if i > 0 and "feedback" in metadata:
                f.write("\nFeedback from previous version:\n")
                feedback = metadata["feedback"]["full_feedback"]
                f.write(feedback + "\n")
                
                # Also check feedback for quoted lines
                for line in feedback.split('\n'):
                    line = line.strip()
                    if line.startswith('"') and line.endswith('"'):
                        last_quoted_line = line
            
            f.write("\n" + "="*50 + "\n")
    
    return last_quoted_line


def translate(input_text):
    # Run iterative translation
    results = iterative_translation(input_text, n_iterations=3)
    opt = save_refinement_history(results)

    return opt
