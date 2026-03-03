# LangChain + Hexarch Guardrails Integration

Protect LangChain applications with policy-driven guardrails for LLM calls, embeddings, and chains.

## Quick Start

```bash
pip install langchain openai hexarch-guardrails
```

## File Structure

```
langchain-app/
├── hexarch.yaml
├── app.py
├── chains.py
└── requirements.txt
```

## hexarch.yaml

```yaml
policies:
  # LLM call protection
  - id: "llm_protection"
    description: "Rate limit and budget for LLM calls"
    rules:
      - resource: "openai_llm"
        requests_per_minute: 60
        monthly_budget: 500
        action: "block"

  # Embedding rate limiting
  - id: "embedding_protection"
    description: "Protect embedding generation"
    rules:
      - resource: "embeddings"
        requests_per_minute: 100
        monthly_budget: 50
        action: "block"

  # Vector store operations
  - id: "vector_store"
    description: "Limit expensive vector operations"
    rules:
      - resource: "similarity_search"
        requests_per_minute: 50
        action: "block"

  # Chain execution limits
  - id: "chain_protection"
    description: "Prevent runaway chain execution"
    rules:
      - resource: "agent_executor"
        max_iterations: 10
        timeout_seconds: 30
        action: "block"
```

## app.py - Basic RAG Application

```python
from langchain.llms import OpenAI
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import CharacterTextSplitter
from langchain.chains import RetrievalQA
from hexarch_guardrails import Guardian

# Initialize guardian
guardian = Guardian()


class GuardedLLM:
    """Wrapper for LangChain LLM with guardrails"""
    
    def __init__(self, policy_id="llm_protection"):
        self.policy_id = policy_id
        self.llm = OpenAI(temperature=0.7)
    
    @guardian.check("llm_protection")
    def __call__(self, prompt: str) -> str:
        """Protected LLM call"""
        return self.llm(prompt)
    
    @guardian.check("llm_protection")
    def generate(self, prompts: list[str]) -> list[str]:
        """Protected batch generation"""
        return self.llm.generate(prompts)


class GuardedEmbeddings:
    """Wrapper for embeddings with guardrails"""
    
    def __init__(self):
        self.embeddings = OpenAIEmbeddings()
    
    @guardian.check("embedding_protection")
    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        """Protected document embedding"""
        return self.embeddings.embed_documents(texts)
    
    @guardian.check("embedding_protection")
    def embed_query(self, text: str) -> list[float]:
        """Protected query embedding"""
        return self.embeddings.embed_query(text)


class GuardedVectorStore:
    """Protected vector store operations"""
    
    def __init__(self, documents: list, embeddings):
        text_splitter = CharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        texts = text_splitter.split_documents(documents)
        self.vectorstore = Chroma.from_documents(texts, embeddings)
    
    @guardian.check("vector_store")
    def similarity_search(self, query: str, k: int = 4):
        """Protected similarity search"""
        return self.vectorstore.similarity_search(query, k=k)
    
    @guardian.check("vector_store")
    def similarity_search_with_score(self, query: str, k: int = 4):
        """Protected similarity search with scores"""
        return self.vectorstore.similarity_search_with_score(query, k=k)


def create_protected_qa_chain():
    """
    Create a RAG chain with guardrails at every step.
    """
    # Load documents
    from langchain.document_loaders import TextLoader
    loader = TextLoader("./documents/data.txt")
    documents = loader.load()
    
    # Protected embeddings
    embeddings = GuardedEmbeddings()
    
    # Protected vector store
    vectorstore = GuardedVectorStore(documents, embeddings)
    
    # Protected LLM
    llm = GuardedLLM()
    
    # Create QA chain
    qa_chain = RetrievalQA.from_chain_type(
        llm=llm.llm,  # Use the underlying LLM
        chain_type="stuff",
        retriever=vectorstore.vectorstore.as_retriever(),
        return_source_documents=True
    )
    
    # Wrap the entire chain
    @guardian.check("chain_protection")
    def protected_query(question: str):
        return qa_chain({"query": question})
    
    return protected_query


# Example usage
if __name__ == "__main__":
    # Simple LLM call
    llm = GuardedLLM()
    
    print("Testing protected LLM call...")
    response = llm("What is the capital of France?")
    print(f"Response: {response}")
    
    # Batch generation
    print("\nTesting batch generation...")
    prompts = [
        "What is AI?",
        "Explain machine learning",
        "What is deep learning?"
    ]
    responses = llm.generate(prompts)
    print(f"Generated {len(responses)} responses")
    
    # RAG chain
    print("\nTesting protected RAG chain...")
    qa = create_protected_qa_chain()
    result = qa("What topics are covered in the documents?")
    print(f"Answer: {result['result']}")
```

## chains.py - Advanced Agent Protection

```python
from langchain.agents import initialize_agent, Tool, AgentType
from langchain.llms import OpenAI
from langchain.utilities import SerpAPIWrapper
from hexarch_guardrails import Guardian

guardian = Guardian()


class ProtectedAgent:
    """
    LangChain agent with guardrails to prevent:
    - Excessive LLM calls
    - Runaway loops
    - Budget overruns
    """
    
    def __init__(self, tools: list[Tool], max_iterations: int = 5):
        self.llm = OpenAI(temperature=0)
        self.agent = initialize_agent(
            tools=tools,
            llm=self.llm,
            agent=AgentType.ZERO_SHOT_REACT_DESCRIPTION,
            max_iterations=max_iterations,
            verbose=True
        )
    
    @guardian.check("chain_protection")
    @guardian.check("llm_protection")
    def run(self, query: str) -> str:
        """
        Execute agent with policy protection.
        
        Policies applied:
        - chain_protection: Max 10 iterations, 30 second timeout
        - llm_protection: Rate limited, budget tracked
        """
        return self.agent.run(query)
    
    @guardian.check("chain_protection")
    @guardian.check("llm_protection")
    async def arun(self, query: str) -> str:
        """Async version with same protections"""
        return await self.agent.arun(query)


def create_protected_agent():
    """Create agent with protected tools"""
    
    # Define tools
    @guardian.check("llm_protection")
    def protected_search(query: str) -> str:
        """Protected web search"""
        search = SerpAPIWrapper()
        return search.run(query)
    
    tools = [
        Tool(
            name="Search",
            func=protected_search,
            description="Search the web for current information"
        ),
        Tool(
            name="Calculator",
            func=lambda x: eval(x),
            description="Perform mathematical calculations"
        )
    ]
    
    return ProtectedAgent(tools=tools)


# Example usage
if __name__ == "__main__":
    agent = create_protected_agent()
    
    # This is protected against:
    # 1. Too many LLM calls
    # 2. Infinite loops
    # 3. Budget overruns
    result = agent.run(
        "What is the current population of Tokyo? "
        "Multiply it by 2 and give me the result."
    )
    
    print(f"Result: {result}")
```

## Streamlit App Example

```python
# streamlit_app.py
import streamlit as st
from langchain.llms import OpenAI
from hexarch_guardrails import Guardian

guardian = Guardian()

st.title("🛡️ Protected LangChain Chatbot")
st.caption("Powered by Hexarch Guardrails")

# Initialize LLM
@st.cache_resource
def get_llm():
    return OpenAI(temperature=0.7)

llm = get_llm()

# Protected chat function
@guardian.check("llm_protection")
def generate_response(prompt: str) -> str:
    """Generate response with rate limiting and budget protection"""
    return llm(prompt)

# Chat interface
if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

if prompt := st.chat_input("Ask me anything..."):
    # Display user message
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)
    
    # Generate and display assistant response
    with st.chat_message("assistant"):
        try:
            response = generate_response(prompt)
            st.markdown(response)
            st.session_state.messages.append({"role": "assistant", "content": response})
        except Exception as e:
            st.error(f"Rate limit exceeded or policy violation: {e}")
            st.info("Please wait a moment and try again.")

# Sidebar with guardian status
with st.sidebar:
    st.header("🛡️ Guardian Status")
    st.metric("Rate Limit", "60 req/min")
    st.metric("Monthly Budget", "$500")
    st.metric("Current Month Spend", "$87.45")
    
    if st.button("Reset Chat"):
        st.session_state.messages = []
        st.rerun()
```

## requirements.txt

```
langchain>=0.1.0
openai>=1.0.0
chromadb>=0.4.0
hexarch-guardrails>=0.4.1
streamlit>=1.30.0
tiktoken>=0.5.0
```

## Run Examples

```bash
# Install dependencies
pip install -r requirements.txt

# Set API keys
export OPENAI_API_KEY="your-key"
export SERPAPI_API_KEY="your-key"  # Optional, for agent example

# Run basic app
python app.py

# Run agent example
python chains.py

# Run Streamlit app
streamlit run streamlit_app.py
```

## Testing Guardrails

### Test 1: Rate Limiting

```python
from app import GuardedLLM

llm = GuardedLLM()

# Fire 65 requests rapidly
for i in range(65):
    try:
        response = llm(f"Count to {i}")
        print(f"✅ Request {i+1} succeeded")
    except Exception as e:
        print(f"🛑 Request {i+1} blocked: {e}")

# Requests after #60 should be blocked
```

### Test 2: Agent Loop Protection

```python
from chains import create_protected_agent

agent = create_protected_agent()

# This query might cause infinite loops without guardrails
try:
    result = agent.run(
        "Keep searching for 'latest news' and summarize, "
        "then search again, repeat 20 times"
    )
except Exception as e:
    print(f"🛡️ Protected from runaway loop: {e}")
```

### Test 3: Budget Protection

```python
from app import GuardedLLM

llm = GuardedLLM()

# Expensive prompts
for i in range(100):
    try:
        response = llm("Write a 2000 word essay about AI" * 10)
    except Exception as e:
        print(f"💵 Budget protection triggered: {e}")
        break
```

## Advanced Patterns

### Custom Callback Handler

```python
from langchain.callbacks.base import BaseCallbackHandler
from hexarch_guardrails import Guardian

guardian = Guardian()


class GuardianCallbackHandler(BaseCallbackHandler):
    """Track all LLM calls through LangChain callback"""
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        """Check policy before LLM call"""
        try:
            guardian.check_policy("llm_protection", resource="openai_llm")
        except Exception as e:
            raise Exception(f"Policy violation: {e}")
    
    def on_llm_end(self, response, **kwargs):
        """Track usage after LLM call"""
        tokens = response.llm_output.get("token_usage", {})
        cost = calculate_cost(tokens)
        guardian.track_usage("openai_llm", cost)


# Use callback with any LangChain component
from langchain.llms import OpenAI

llm = OpenAI(callbacks=[GuardianCallbackHandler()])
```

## Production Considerations

1. **Persistent state**: Use Redis/PostgreSQL for rate limit tracking
2. **Cost tracking**: Implement actual token counting and cost calculation
3. **Monitoring**: Add logging for all policy violations
4. **Alerts**: Set up notifications for budget thresholds

## Links

- [LangChain Documentation](https://python.langchain.com/)
- [Hexarch Guardrails](https://github.com/no1rstack/hexarch-guardrails)
- [OpenAI Pricing](https://openai.com/pricing)
