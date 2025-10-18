# Custom Model Configuration

## Overview

The chatbot now supports using custom model endpoints, not just OpenAI. You can configure any OpenAI-compatible API endpoint, including local models, Groq, Together AI, or other providers.

## Configuration

### Environment Variable

Add the `LLM_BASE_URL` environment variable to your `.env` file:

```bash
# Use Groq
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_API_KEY="your-groq-api-key"
LLM_MODEL="mixtral-8x7b-32768"

# Or use local Ollama
LLM_BASE_URL="http://localhost:11434/v1"
LLM_API_KEY="ollama"  # Ollama doesn't require a real key
LLM_MODEL="llama2"

# Or use Together AI
LLM_BASE_URL="https://api.together.xyz/v1"
LLM_API_KEY="your-together-api-key"
LLM_MODEL="mistralai/Mixtral-8x7B-Instruct-v0.1"

# Or use OpenAI (default, LLM_BASE_URL not needed)
LLM_API_KEY="your-openai-api-key"
LLM_MODEL="gpt-4o-mini"
```

## Supported Providers

### OpenAI (Default)
```bash
LLM_BASE_URL=""  # Leave empty or omit
LLM_MODEL="gpt-4o-mini"
```

### Groq (Fast Inference)
```bash
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_MODEL="mixtral-8x7b-32768"
```

Available Groq models:
- `mixtral-8x7b-32768` - Mixtral 8x7B
- `llama2-70b-4096` - LLaMA 2 70B
- `gemma-7b-it` - Gemma 7B

### Ollama (Local Models)
```bash
LLM_BASE_URL="http://localhost:11434/v1"
LLM_MODEL="llama2"
```

First, install and run Ollama:
```bash
# Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model
ollama pull llama2

# Run Ollama server (it runs by default)
ollama serve
```

### Together AI
```bash
LLM_BASE_URL="https://api.together.xyz/v1"
LLM_MODEL="mistralai/Mixtral-8x7B-Instruct-v0.1"
```

### Anthropic (via OpenAI-compatible proxy)
Some services provide OpenAI-compatible proxies for Anthropic models.

## How It Works

The application uses LangChain's `ChatOpenAI` class, which supports any OpenAI-compatible API. When you set `LLM_BASE_URL`, it overrides the default OpenAI endpoint.

### Code Implementation

```python
# In app/core/langgraph/graph.py
model_kwargs = self._get_model_kwargs()

if settings.LLM_BASE_URL:
    model_kwargs["base_url"] = settings.LLM_BASE_URL
    logger.info("using_custom_llm_url", base_url=settings.LLM_BASE_URL)

self.llm = ChatOpenAI(
    model=settings.LLM_MODEL,
    temperature=settings.DEFAULT_LLM_TEMPERATURE,
    api_key=settings.LLM_API_KEY,
    max_tokens=settings.MAX_TOKENS,
    **model_kwargs,
)
```

## Testing Custom Models

1. **Update your `.env` file** with the custom model configuration
2. **Restart the application**
3. **Check logs** for the message: "using_custom_llm_url"
4. **Send a test message** in the chat interface

## Compatibility Notes

- The custom endpoint must be OpenAI API-compatible
- Not all models support function calling (required for tools)
- Some models may have different token limits
- Adjust `MAX_TOKENS` based on your model's capabilities

## Common Issues

### Issue: "Model not found"
**Solution:** Check that the model name is correct for your provider

### Issue: "Authentication failed"
**Solution:** Verify your API key is correct for the provider

### Issue: "Tool/function calls not working"
**Solution:** Not all models support function calling. Consider:
- Using a model that supports function calling
- Disabling tools in your application
- Using OpenAI models which fully support tools

## Cost Optimization

Using alternative providers can significantly reduce costs:

- **Groq**: Very fast inference, competitive pricing
- **Ollama**: Free for local hosting (uses your hardware)
- **Together AI**: Often cheaper than OpenAI for open-source models

## Performance Comparison

| Provider | Speed | Cost | Function Calling |
|----------|-------|------|------------------|
| OpenAI GPT-4o-mini | Fast | $$ | ✅ Full support |
| Groq Mixtral | Very Fast | $ | ⚠️ Limited |
| Ollama Local | Depends on hardware | Free | ⚠️ Limited |
| Together AI | Fast | $ | ⚠️ Varies by model |

## Example Configurations

### Development (Local + Free)
```bash
LLM_BASE_URL="http://localhost:11434/v1"
LLM_MODEL="llama2"
LLM_API_KEY="ollama"
```

### Production (Groq for Speed)
```bash
LLM_BASE_URL="https://api.groq.com/openai/v1"
LLM_MODEL="mixtral-8x7b-32768"
LLM_API_KEY="gsk_..."
```

### Production (OpenAI for Quality)
```bash
LLM_BASE_URL=""
LLM_MODEL="gpt-4o-mini"
LLM_API_KEY="sk-..."
```

