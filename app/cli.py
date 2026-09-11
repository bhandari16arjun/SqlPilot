import os
from dotenv import load_dotenv
from app.agent.graph import create_graph

# Load environment variables (like GEMINI_API_KEY)
load_dotenv()

def main():
    print("===========================================")
    print("   Welcome to SQLPilot (Phase 1: Core)     ")
    print("===========================================")
    print("Type 'exit' or 'quit' to close the app.\n")
    
    graph = create_graph()
    
    while True:
        question = input("\nAsk a question about your customers or subscriptions: ")
        if question.lower() in ['exit', 'quit']:
            break
            
        initial_state = {
            "user_question": question,
            "schema_context": "",
            "generated_sql": None,
            "execution_results": None,
            "final_answer": None
        }
        
        try:
            # Run the LangGraph state machine
            result_state = graph.invoke(initial_state)
            
            print("\n" + "="*50)
            print(f"🚀 GENERATED SQL:\n{result_state['generated_sql']}")
            print("-" * 50)
            print(f"💾 RAW DATABASE RESULTS:\n{result_state['execution_results']}")
            print("-" * 50)
            print(f"🤖 AI EXPLANATION:\n{result_state['final_answer']}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
