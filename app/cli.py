import os
import uuid
from dotenv import load_dotenv

# Load environment variables FIRST, before importing anything else
load_dotenv()

from app.agent.graph import create_graph

def main():
    print("===========================================")
    print("   Welcome to SQLPilot (Phase 3: Clarify)  ")
    print("===========================================")
    print("Type 'exit' or 'quit' to close the app.")
    print("Type '/remember <rule>' to save a persistent preference (e.g., /remember Always use UPPERCASE for emails).\n")
    
    graph = create_graph()
    
    while True:
        question = input("\nAsk a question about your customers or subscriptions: ")
        if question.lower() in ['exit', 'quit']:
            break
            
        if question.lower().startswith("/remember "):
            rule = question[10:].strip()
            from app.agent.memory import PreferenceManager
            PreferenceManager().add_rule(rule)
            print(f"✅ Saved persistent preference: '{rule}'")
            continue
            
        initial_state = {
            "user_question": question,
            "schema_context": "",
            "is_ambiguous": False,
            "clarification_question": "",
            "conversation_history": [],
            "generated_sql": None,
            "error_message": None,
            "retry_count": 0,
            "execution_results": None,
            "final_answer": None
        }
        
        # Initialize Langfuse Callback for Tracing
        try:
            from langfuse.langchain import CallbackHandler
            langfuse_handler = CallbackHandler()
            callbacks = [langfuse_handler]
        except Exception as e:
            print(f"Warning: Langfuse tracing disabled. {e}")
            callbacks = []

        # Unique thread ID for this conversation (required for MemorySaver to work)
        config = {
            "configurable": {"thread_id": str(uuid.uuid4())},
            "callbacks": callbacks
        }
        
        try:
            # We use stream so we can catch the interrupt
            for event in graph.stream(initial_state, config):
                pass
                
            # Check the current state of the graph
            state = graph.get_state(config)
            
            # Loop as long as the graph is paused at the 'clarify' node
            while state.next and state.next[0] == "clarify":
                current_values = state.values
                clarification_q = current_values.get("clarification_question")
                
                print(f"\n[AI Needs Clarification] 🤔 {clarification_q}")
                user_answer = input("Your answer: ")
                
                # Append to history
                history = current_values.get("conversation_history", [])
                history.append(f"AI: {clarification_q}\nUser: {user_answer}")
                
                # Update the state directly
                graph.update_state(config, {"conversation_history": history, "is_ambiguous": False})
                
                # Resume execution with None
                for event in graph.stream(None, config):
                    pass
                    
                state = graph.get_state(config)

            # Execution is finished!
            final_state = state.values
            print("\n" + "="*50)
            print(f"🚀 GENERATED SQL:\n{final_state.get('generated_sql')}")
            print("-" * 50)
            print(f"💾 RAW DATABASE RESULTS:\n{final_state.get('execution_results')}")
            print("-" * 50)
            print(f"🤖 AI EXPLANATION:\n{final_state.get('final_answer')}")
            print("="*50 + "\n")
            
        except Exception as e:
            print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
