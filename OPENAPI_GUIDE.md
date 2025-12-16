# OpenAPI Documentation

This directory contains OpenAPI 3.0 specification for the MediAssist API.

## Files

- `openapi.yaml` - OpenAPI specification in YAML format
- `openapi.json` - OpenAPI specification in JSON format (generated)

## Viewing the Documentation

### Option 1: Swagger UI (Recommended)

**Online:**
1. Go to https://editor.swagger.io/
2. File → Import File → Select `openapi.yaml`
3. View interactive documentation

**Local:**
```bash
# Using npx (no installation required)
npx @redocly/cli preview-docs openapi.yaml

# Or install swagger-ui-watcher
npm install -g swagger-ui-watcher
swagger-ui-watcher openapi.yaml
```

### Option 2: Redoc

**Online:**
```bash
npx @redocly/cli preview-docs openapi.yaml
```

**Generate static HTML:**
```bash
npx @redocly/cli build-docs openapi.yaml -o docs/index.html
```

### Option 3: Postman

1. Open Postman
2. Import → Link/File
3. Select `openapi.yaml`
4. Auto-generates collection with all endpoints

### Option 4: VS Code Extension

Install **OpenAPI (Swagger) Editor** extension:
1. Install extension: `42Crunch.vscode-openapi`
2. Open `openapi.yaml`
3. View documentation in split pane

## Using the Spec

### Generate Client SDKs

**TypeScript/JavaScript:**
```bash
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g typescript-axios \
  -o ./clients/typescript
```

**Python:**
```bash
npx @openapitools/openapi-generator-cli generate \
  -i openapi.yaml \
  -g python \
  -o ./clients/python
```

**Other Languages:**
- Java: `-g java`
- C#: `-g csharp`
- Go: `-g go`
- Ruby: `-g ruby`
- PHP: `-g php`
- And 50+ more...

### Validate the Spec

```bash
# Using Redocly
npx @redocly/cli lint openapi.yaml

# Using Swagger
npx @apidevtools/swagger-cli validate openapi.yaml
```

### Generate Postman Collection

```bash
npx openapi-to-postmanv2 \
  -s openapi.yaml \
  -o postman-collection.json
```

### Mock Server

Start a mock server based on the OpenAPI spec:

```bash
# Using Prism
npx @stoplight/prism-cli mock openapi.yaml

# Server starts at http://localhost:4010
```

## Quick Examples

### cURL Examples

**Chat Request:**
```bash
curl -X POST http://localhost:3000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What are the side effects of ibuprofen?"
  }'
```

**Health Check:**
```bash
curl http://localhost:3000/agent/health
```

### JavaScript/Fetch

```javascript
const response = await fetch('http://localhost:3000/agent/chat', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    message: 'What are the side effects of ibuprofen?'
  })
});

const data = await response.json();
console.log(data.answer);
```

### Python/Requests

```python
import requests

response = requests.post(
    'http://localhost:3000/agent/chat',
    json={'message': 'What are the side effects of ibuprofen?'}
)

print(response.json()['answer'])
```

## API Overview

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/agent/chat` | Send message to pharmacy assistant |
| GET | `/agent/health` | Health check endpoint |
| GET | `/` | API information |

### Request/Response Examples

**Valid Query:**
```json
Request:
{
  "message": "What are the side effects of ibuprofen?"
}

Response:
{
  "answer": "Based on FDA drug label data, ibuprofen may cause nausea, heartburn, dizziness...\n\n⚠️ SAFETY DISCLAIMER: ..."
}
```

**Refused Query:**
```json
Request:
{
  "message": "How much should I take?"
}

Response:
{
  "answer": "I cannot provide personal dosage recommendations. Medication dosing must be determined by a healthcare professional..."
}
```

**Validation Error:**
```json
Request:
{
  "message": ""
}

Response (400):
{
  "error": "Invalid request",
  "details": [
    {
      "field": "message",
      "message": "Message cannot be empty"
    }
  ]
}
```

## Schema Validation

The OpenAPI spec includes:

- ✅ Request validation (message: 1-1000 characters)
- ✅ Response schemas for all endpoints
- ✅ Error response schemas
- ✅ Comprehensive examples
- ✅ Detailed descriptions

## Integration Testing

Use the OpenAPI spec for automated testing:

```bash
# Using Dredd
npm install -g dredd
dredd openapi.yaml http://localhost:3000
```

## CI/CD Integration

Add to your CI pipeline:

```yaml
# .github/workflows/api-docs.yml
name: Validate OpenAPI

on: [push, pull_request]

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Validate OpenAPI
        run: npx @redocly/cli lint openapi.yaml
```

## Documentation Hosting

Host the API documentation:

```bash
# Build static docs
npx @redocly/cli build-docs openapi.yaml -o docs/index.html

# Serve locally
python -m http.server 8080 --directory docs

# Or use GitHub Pages
# Push docs/ directory to gh-pages branch
```

## Updates

When updating the API:

1. Update `openapi.yaml`
2. Validate: `npx @redocly/cli lint openapi.yaml`
3. Test: `dredd openapi.yaml http://localhost:3000`
4. Generate new client SDKs if needed
5. Update version number in spec

## Additional Resources

- [OpenAPI Specification](https://swagger.io/specification/)
- [Swagger Editor](https://editor.swagger.io/)
- [Redoc](https://redocly.com/redoc/)
- [OpenAPI Generator](https://openapi-generator.tech/)
- [Prism Mock Server](https://stoplight.io/open-source/prism)

## Support

For API questions, see:
- `../USAGE.md` - Complete usage guide
- `../EXAMPLES.md` - API request examples
- `../ARCHITECTURE.md` - System architecture
