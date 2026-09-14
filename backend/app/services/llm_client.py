def generate_explanation(prompt, llm_function):
    if llm_function is None:
        raise ValueError("LLM function is required.")

    return llm_function(prompt)