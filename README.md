# MediAssist Backend

A production-ready agentic pharmacy assistant backend powered by **Gemini Function Calling** and **openFDA Drug Label API**.

## 🏗️ Architecture

This system implements a **Reason → Act → Observe → Synthesize** agent loop using:

- **Gemini API**: Reasoning engine ("brain") with function calling
- **openFDA API**: Authoritative drug data source ("hands")
- **Clean Architecture**: Hexagonal pattern with clear separation of concerns

## 🚀 Tech Stack

- Node.js + TypeScript
- Express.js
- Gemini API (function calling)
- openFDA Drug Label API
- Zod (validation)
- Axios (HTTP client)

## 📁 Project Structure

```
src/
 ├── app.ts                   # Express app configuration
 ├── server.ts                # Server entry point
 ├── config/
 │    ├── env.ts              # Environment variables validation
 │    └── gemini.ts           # Gemini client setup
 ├── agent/
 │    ├── agent.service.ts    # Core agent orchestration logic
 │    ├── agent.prompt.ts     # System prompts and safety rules
 │    └── agent.types.ts      # Agent-related types
 ├── tools/
 │    └── openfda.tool.ts     # OpenFDA API integration
 ├── domain/
 │    ├── drug.entity.ts      # Drug domain entities
 │    └── drug.mapper.ts      # FDA data mapping logic
 ├── api/
 │    └── agent.controller.ts # Express routes and controllers
 └── utils/
      ├── normalizeDrugName.ts # Drug name normalization
      └── logger.ts            # Application logging
```

## 🔧 Setup

1. **Clone and install dependencies:**
   ```bash
   npm install
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env and add your GEMINI_API_KEY
   ```

3. **Run in development:**
   ```bash
   npm run dev
   ```

4. **Build for production:**
   ```bash
   npm run build
   npm start
   ```

## 🎯 API Usage

### Endpoint

```
POST /agent/chat
```

### Request

```json
{
  "message": "What are the side effects of paracetamol?"
}
```

### Response

```json
{
  "answer": "Based on FDA drug label data, acetaminophen (paracetamol) may cause side effects including...\n\n⚠️ SAFETY DISCLAIMER: This information is for educational purposes only..."
}
```

## 🛡️ Safety Features

- **No Hallucination**: Only uses verified FDA data
- **Safety Rules**: Refuses sensitive queries (children, pregnancy, exact dosage)
- **Name Normalization**: Handles common drug name variations
- **Disclaimer**: Always includes medical safety warnings

## 🧠 How It Works

1. **Reason**: Gemini analyzes user intent and decides if FDA data is needed
2. **Act**: If needed, calls openFDA API with appropriate parameters
3. **Observe**: Receives structured FDA data
4. **Synthesize**: Gemini creates human-readable response with safety disclaimers

## � API Documentation

Interactive OpenAPI documentation is available:

```bash
# View in Swagger UI
npx @redocly/cli preview-docs openapi.yaml

# Or open in online editor
# Visit: https://editor.swagger.io/
# Import: openapi.yaml
```

See `OPENAPI_GUIDE.md` for:
- Viewing the documentation
- Generating client SDKs
- Integration testing
- Mock server setup

## �📝 License

MIT
