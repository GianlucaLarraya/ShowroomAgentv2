from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser

def create_chat_interface():
    """Crea una interfaz de chat interactiva con el LLM"""
    
    # Inicializar el modelo
    llm = ChatOpenAI(model="gpt-4o", temperature=0.7)
    
    # Historial de mensajes para mantener contexto
    chat_history = []
    
    print("🤖 Chat con IA iniciado!")
    print("Escribe 'salir' para terminar la conversación")
    print("Escribe 'limpiar' para borrar el historial de chat")
    print("-" * 50)
    
    while True:
        # Obtener input del usuario
        user_input = input("\n👤 Tú: ").strip()
        
        # Verificar comandos especiales
        if user_input.lower() == 'salir':
            print("👋 ¡Hasta luego!")
            break
        elif user_input.lower() == 'limpiar':
            chat_history.clear()
            print("🧹 Historial de chat limpiado")
            continue
        elif not user_input:
            continue
        
        try:
            # Crear mensaje del usuario
            user_message = HumanMessage(content=user_input)
            
            # Agregar mensaje del usuario al historial
            chat_history.append(user_message)
            
            # Obtener respuesta del LLM con contexto del historial
            response = llm.invoke(chat_history)
            
            # Agregar respuesta del AI al historial
            chat_history.append(response)
            
            # Mostrar respuesta
            print(f"\n🤖 IA: {response.content}")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            print("Intenta de nuevo...")

if __name__ == "__main__":
    create_chat_interface() 