# ServiBot Frontend

Interfaz de usuario moderna para ServiBot - Agente Autónomo Multimodal con IA.

## 🚀 Características

- ✅ **Chat conversacional** con historial y auto-scroll
- ✅ **Timeline del agente** para visualizar pasos de ejecución
- ✅ **Upload de archivos** con drag & drop y barra de progreso
- ✅ **Grabación de voz** con Whisper (transcripción)
- ✅ **Text-to-Speech** con ElevenLabs/gTTS
- ✅ **Renderizado de Markdown** con sanitización
- ✅ **Diseño responsive** (mobile-first)
- ✅ **Accesibilidad** (ARIA labels, keyboard navigation)
- ✅ **Tests** con Vitest y Testing Library

## 📦 Tech Stack

- **React 18** - Framework UI
- **Vite** - Build tool y dev server
- **Tailwind CSS** - Estilos utility-first
- **Zustand** - State management
- **Axios** - Cliente HTTP
- **React Markdown** - Renderizado de Markdown
- **Lucide React** - Iconos
- **Vitest** - Testing framework
- **Testing Library** - Component testing

## 🛠️ Instalación

```bash
# Clonar repositorio
git clone <repo-url>
cd ServiBot/frontend

# Instalar dependencias
npm install

# Copiar variables de entorno
cp .env.example .env

# Configurar URL del backend en .env
VITE_API_URL=http://localhost:8000
```

## 🏃 Desarrollo

```bash
# Iniciar servidor de desarrollo
npm run dev

# Build para producción
npm run build

# Preview de build de producción
npm run preview
```

El servidor de desarrollo estará disponible en `http://localhost:3000`

## 🧪 Testing

```bash
# Ejecutar tests
npm run test

# Ejecutar tests en modo UI
npm run test:ui

# Ejecutar tests una vez (CI)
npm run test:run

# Generar coverage
npm run coverage
```

## 🎨 Linting y Formato

```bash
# Lint
npm run lint

# Lint con auto-fix
npm run lint:fix

# Format con Prettier
npm run format

# Check formato
npm run format:check
```

## 📁 Estructura del Proyecto

```
src/
├── components/        # Componentes React
│   ├── ChatInterface.jsx
│   ├── FileUpload.jsx
│   ├── VoiceRecorder.jsx
│   ├── AgentTimeline.jsx
│   ├── MarkdownRenderer.jsx
│   └── ui/           # Componentes UI reutilizables
├── hooks/            # Custom hooks
│   ├── useChat.js
│   ├── useFileUpload.js
│   └── useToast.js
├── services/         # API services
│   ├── api.js        # Cliente HTTP central
│   └── index.js      # Servicios específicos
├── store/            # Zustand stores
│   └── index.js
├── types/            # Type definitions (JSDoc)
│   └── api.js
├── tests/            # Tests
│   ├── setup.js
│   └── components/
└── App.jsx           # Root component
```

## 🔌 Integración con Backend

El frontend consume los siguientes endpoints del backend:

### Chat
- `POST /api/chat` - Enviar mensaje al agente

### Upload
- `POST /api/upload` - Subir archivo
- `GET /api/upload/status/{file_id}` - Estado de indexación
- `POST /api/upload/reindex/{file_id}` - Reindexar archivo

### Voice
- `POST /api/voice/transcribe` - Transcribir audio (Whisper)
- `POST /api/voice/synthesize` - Sintetizar voz (TTS)

Ver [src/types/api.js](src/types/api.js) para contratos completos.

## 🌐 Deploy

### Vercel (Recomendado)

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel

# Deploy a producción
vercel --prod
```

Configurar variables de entorno en Vercel:
- `VITE_API_URL` - URL del backend (ej: `https://servibot-backend.onrender.com`)

## 📝 Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| `VITE_API_URL` | URL del backend API | `http://localhost:8000` |

## 🎯 Roadmap

- [x] Chat conversacional básico
- [x] Upload de archivos
- [x] Voice recording + transcription
- [x] Text-to-speech
- [x] Agent timeline
- [x] Markdown rendering
- [x] Tests básicos
- [ ] Dark/Light theme toggle
- [ ] Streaming responses
- [ ] PWA support
- [ ] Internationalization (i18n)

## 🐛 Troubleshooting

### El build falla

```bash
# Limpiar cache y node_modules
rm -rf node_modules dist .vite
npm install
npm run build
```

### Tests fallan

```bash
# Verificar setup de tests
npm run test -- --reporter=verbose
```

### CORS errors

Asegúrate de que el backend tenga configurado CORS correctamente:

```python
# backend/app/main.py
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## 📄 Licencia

Este proyecto es parte del TFG de Rafa Castaño (Enero 2026).

## 🤝 Contribuir

1. Fork el proyecto
2. Crea tu feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la branch (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

---

**Desarrollado con ❤️ para el proyecto ServiBot**
