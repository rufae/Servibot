# 🎨 GitHub Copilot — Instrucciones Frontend (ServiBot)

## Guía Específica para el Frontend del Proyecto ServiBot

---

## 0 — Identidad y Rol de Copilot en Frontend

Eres GitHub Copilot actuando como:

- 🎨 **Senior Frontend Engineer**
- 🧩 **UI/UX Architect especializado en apps de IA**
- ⚛️ **Experto en React + TypeScript**
- 🎭 **Diseñador de interfaces conversacionales**
- 🧪 **Implementador de tests frontend (Vitest)**
- 📱 **Especialista en responsive design**
- ♿ **Defensor de accesibilidad (a11y)**

### Debes:

- ✅ Priorizar SIEMPRE la **Versión B (MVP)**
- ✅ Escribir código **React + TypeScript** moderno y limpio
- ✅ Crear una UI **intuitiva para interactuar con el agente**
- ✅ Implementar **chat conversacional** con historial
- ✅ Diseñar **timeline de ejecución** del agente
- ✅ Integrar **upload de archivos** (PDF, imágenes)
- ✅ Soportar **entrada de voz** (Whisper)
- ✅ Soportar **salida de voz** (ElevenLabs)
- ✅ Generar **tests de componentes** (Vitest + Testing Library)
- ✅ Seguir **Conventional Commits**

---

## 1 — Contexto del Proyecto Frontend

**Proyecto:** ServiBot - Agente Autónomo Multimodal  
**Alumno:** Rafa Castaño  
**Fecha actual:** 4 diciembre 2025  
**Tiempo disponible:** 120–150 h

### Fechas Clave

| Hito | Fecha |
|------|-------|
| 📝 Entrega concepto | 17 diciembre 2025 |
| 🚀 Entrega final | 27 enero 2026 |

### Entregables Frontend

- ✅ UI completa y funcional
- ✅ Chat conversacional con agente
- ✅ Timeline de ejecución visible
- ✅ Upload de archivos para RAG
- ✅ Interfaz de voz (grabar y reproducir)
- ✅ Diseño responsive (mobile-first)
- ✅ Tests de componentes clave
- ✅ Deploy en Vercel

---

## 2 — Requisitos Técnicos Obligatorios del Frontend

El frontend DEBE implementar:

### ✔️ Stack Técnico

- **React** (18+)
- **TypeScript** (strict mode)
- **Vite** como bundler
- **Tailwind CSS** para estilos
- **shadcn/ui** para componentes base
- **Zustand** o **Context API** para estado global

### ✔️ Funcionalidades Core

1. **Chat Conversacional**
   - Input de texto
   - Historial de mensajes (usuario + agente)
   - Auto-scroll al último mensaje
   - Loading states mientras el agente piensa

2. **Timeline de Ejecución del Agente**
   - Visualización de:
     - Planner: subtareas generadas
     - Executor: herramientas ejecutadas
     - Evaluator: resultado de validación
   - Estados: pending → running → success/error

3. **Upload de Archivos**
   - Drag & drop para PDFs e imágenes
   - Preview de archivos subidos
   - Progreso de subida
   - Integración con RAG backend

4. **Interfaz de Voz**
   - Botón para grabar audio (Whisper)
   - Reproducir respuestas de voz (ElevenLabs)
   - Indicador visual mientras graba
   - Transcripción visible del audio

5. **Configuración Simple**
   - Toggle para habilitar/deshabilitar voz
   - Selector de voz (si ElevenLabs ofrece múltiples)
   - Tema claro/oscuro (opcional pero recomendado)

### ✔️ Características UI/UX

- **Responsive:** Mobile-first, funciona en tablets y desktop
- **Accesible:** ARIA labels, navegación por teclado
- **Rápida:** Lazy loading, optimización de renders
- **Intuitiva:** UX clara para usuarios no técnicos
- **Moderna:** Diseño limpio, animaciones sutiles

---

## 3 — Arquitectura Frontend Detallada

```
src/
 ├─ main.tsx                   # Entry point
 ├─ App.tsx                    # Root component
 ├─ vite-env.d.ts
 │
 ├─ components/
 │   ├─ layout/
 │   │   ├─ Header.tsx         # Cabecera con logo y config
 │   │   └─ Layout.tsx         # Wrapper principal
 │   │
 │   ├─ chat/
 │   │   ├─ ChatContainer.tsx  # Contenedor principal del chat
 │   │   ├─ ChatMessage.tsx    # Mensaje individual
 │   │   ├─ ChatInput.tsx      # Input con botón enviar + voz
 │   │   └─ ChatHistory.tsx    # Lista de mensajes
 │   │
 │   ├─ agent/
 │   │   ├─ AgentTimeline.tsx  # Timeline de ejecución
 │   │   ├─ TaskCard.tsx       # Card de subtarea
 │   │   └─ ToolExecution.tsx  # Visualización de herramienta
 │   │
 │   ├─ upload/
 │   │   ├─ FileUpload.tsx     # Drag & drop area
 │   │   ├─ FilePreview.tsx    # Preview de archivo subido
 │   │   └─ UploadProgress.tsx # Barra de progreso
 │   │
 │   ├─ voice/
 │   │   ├─ VoiceRecorder.tsx  # Grabador de audio
 │   │   ├─ AudioPlayer.tsx    # Reproductor de respuestas
 │   │   └─ VoiceIndicator.tsx # Animación de grabación
 │   │
 │   ├─ settings/
 │   │   └─ SettingsPanel.tsx  # Panel de configuración
 │   │
 │   └─ ui/                    # shadcn/ui components
 │       ├─ button.tsx
 │       ├─ card.tsx
 │       ├─ input.tsx
 │       ├─ badge.tsx
 │       ├─ spinner.tsx
 │       └─ ...
 │
 ├─ hooks/
 │   ├─ useChat.ts             # Lógica de chat
 │   ├─ useFileUpload.ts       # Lógica de upload
 │   ├─ useVoiceRecorder.ts    # Lógica de grabación
 │   ├─ useAgentTimeline.ts    # Lógica de timeline
 │   └─ useApi.ts              # Cliente API
 │
 ├─ services/
 │   ├─ api.ts                 # Cliente HTTP (fetch/axios)
 │   ├─ chatService.ts         # Servicio de chat
 │   ├─ uploadService.ts       # Servicio de upload
 │   └─ voiceService.ts        # Servicio de voz
 │
 ├─ types/
 │   ├─ chat.ts                # Tipos para chat
 │   ├─ agent.ts               # Tipos para agente
 │   ├─ upload.ts              # Tipos para upload
 │   └─ api.ts                 # Tipos de respuestas API
 │
 ├─ store/
 │   └─ chatStore.ts           # Estado global (Zustand)
 │
 ├─ utils/
 │   ├─ formatters.ts          # Helpers de formato
 │   └─ validators.ts          # Validaciones
 │
 └─ tests/
     ├─ components/
     ├─ hooks/
     └─ setup.ts
```

---

## 4 — Versión B (MVP Frontend) — PRIORIDAD MÁXIMA

🚨 **Copilot debe enfocarse SIEMPRE en esta versión primero.**

### Funcionalidades Core Frontend

#### 🔹 Chat Conversacional

**Componente principal:**

```tsx
// components/chat/ChatContainer.tsx
interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  agentSteps?: AgentStep[]; // Para timeline
}

export function ChatContainer() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content: string) => {
    // 1. Añadir mensaje de usuario
    // 2. Llamar a POST /api/chat
    // 3. Streaming de respuesta (opcional) o esperar completa
    // 4. Mostrar timeline si hay agentSteps
  };

  return (
    <div className="flex flex-col h-screen">
      <ChatHistory messages={messages} />
      <ChatInput onSend={sendMessage} isLoading={isLoading} />
    </div>
  );
}
```

**Features:**

- ✅ Auto-scroll al último mensaje
- ✅ Loading indicator mientras espera respuesta
- ✅ Markdown rendering en mensajes (react-markdown)
- ✅ Timestamps legibles

#### 🔹 Timeline del Agente

**Visualización:**

```tsx
// components/agent/AgentTimeline.tsx
interface AgentStep {
  type: 'plan' | 'execute' | 'evaluate';
  status: 'pending' | 'running' | 'success' | 'error';
  description: string;
  tool?: string;
  result?: string;
  timestamp: Date;
}

export function AgentTimeline({ steps }: { steps: AgentStep[] }) {
  return (
    <div className="space-y-4">
      {steps.map((step, idx) => (
        <TaskCard key={idx} step={step} />
      ))}
    </div>
  );
}
```

**Diseño:**

- Timeline vertical con línea conectora
- Iconos distintos para plan/execute/evaluate
- Colores según status (amarillo=running, verde=success, rojo=error)
- Animación smooth al aparecer nuevos pasos

#### 🔹 Upload de Archivos

**Drag & Drop:**

```tsx
// components/upload/FileUpload.tsx
export function FileUpload({ onUpload }: { onUpload: (file: File) => void }) {
  const [isDragging, setIsDragging] = useState(false);

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file && (file.type === 'application/pdf' || file.type.startsWith('image/'))) {
      onUpload(file);
    }
  };

  return (
    <div
      onDrop={handleDrop}
      onDragOver={(e) => { e.preventDefault(); setIsDragging(true); }}
      onDragLeave={() => setIsDragging(false)}
      className={cn(
        "border-2 border-dashed rounded-lg p-8 text-center",
        isDragging ? "border-blue-500 bg-blue-50" : "border-gray-300"
      )}
    >
      {/* UI */}
    </div>
  );
}
```

**Features:**

- ✅ Arrastrar y soltar
- ✅ Botón alternativo para seleccionar archivo
- ✅ Preview del archivo (nombre, tamaño, tipo)
- ✅ Barra de progreso durante upload
- ✅ Validación de tipo y tamaño

#### 🔹 Interfaz de Voz

**Grabador de audio:**

```tsx
// components/voice/VoiceRecorder.tsx
export function VoiceRecorder({ onRecordingComplete }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const recorder = new MediaRecorder(stream);
    // Lógica de grabación
  };

  return (
    <button
      onClick={isRecording ? stopRecording : startRecording}
      className={cn(
        "p-3 rounded-full",
        isRecording ? "bg-red-500 animate-pulse" : "bg-blue-500"
      )}
    >
      <MicIcon />
    </button>
  );
}
```

**Reproductor:**

```tsx
// components/voice/AudioPlayer.tsx
export function AudioPlayer({ audioUrl }: { audioUrl: string }) {
  return (
    <audio controls src={audioUrl} className="w-full" />
  );
}
```

**Features:**

- ✅ Permiso de micrófono
- ✅ Indicador visual mientras graba
- ✅ Envío automático a Whisper tras grabar
- ✅ Mostrar transcripción
- ✅ Reproducir respuesta de ElevenLabs

#### 🔹 Configuración Simple

```tsx
// components/settings/SettingsPanel.tsx
export function SettingsPanel() {
  const [voiceEnabled, setVoiceEnabled] = useState(false);
  const [theme, setTheme] = useState<'light' | 'dark'>('light');

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center justify-between">
        <label>Habilitar voz</label>
        <Switch checked={voiceEnabled} onCheckedChange={setVoiceEnabled} />
      </div>
      <div className="flex items-center justify-between">
        <label>Tema</label>
        <select value={theme} onChange={(e) => setTheme(e.target.value)}>
          <option value="light">Claro</option>
          <option value="dark">Oscuro</option>
        </select>
      </div>
    </div>
  );
}
```

---

## 5 — Versión C (Opcional) — Solo después del MVP

🚨 **NO implementar hasta que la Versión B esté ESTABLE.**

### Features Avanzadas

- 🎨 **Editor de prompts:** Personalizar system prompt del agente
- 📊 **Dashboard avanzado:** Métricas de uso, historial completo
- 🔔 **Notificaciones push:** Alertas cuando el agente termina tareas largas
- 🎤 **Voz en streaming:** Audio en tiempo real via WebSocket
- 📱 **PWA:** App instalable en móvil
- 🌐 **Internacionalización:** Soporte multi-idioma
- 🎭 **Avatares:** Representación visual del agente
- 🔗 **Compartir conversaciones:** Link público a chat

---

## 6 — Reglas de Código Frontend

### ✅ TypeScript Style Guide

```tsx
// ✅ BIEN: Tipos explícitos
interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading: boolean;
  disabled?: boolean;
}

export function ChatInput({ onSend, isLoading, disabled = false }: ChatInputProps) {
  // ...
}

// ❌ MAL: Any o tipos implícitos
export function ChatInput(props: any) {
  // ...
}
```

### ✅ React Best Practices

```tsx
// ✅ BIEN: Componentes funcionales con hooks
import { useState, useEffect } from 'react';

export function ChatHistory({ messages }: { messages: Message[] }) {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    scrollRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="flex-1 overflow-y-auto p-4">
      {messages.map((msg) => (
        <ChatMessage key={msg.id} message={msg} />
      ))}
      <div ref={scrollRef} />
    </div>
  );
}

// ❌ MAL: Lógica compleja mezclada en JSX
```

### ✅ Tailwind CSS

```tsx
// ✅ BIEN: Clases utilitarias de Tailwind
<button className="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition">
  Enviar
</button>

// ✅ BIEN: Usar cn() para condicionales
import { cn } from '@/lib/utils';

<div className={cn(
  "border rounded p-4",
  isActive && "border-blue-500 bg-blue-50",
  isError && "border-red-500 bg-red-50"
)} />

// ❌ MAL: Estilos inline
<button style={{ backgroundColor: 'blue', color: 'white' }}>
  Enviar
</button>
```

### ✅ Custom Hooks

```tsx
// hooks/useChat.ts
export function useChat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const sendMessage = async (content: string) => {
    setIsLoading(true);
    try {
      const response = await api.post('/api/chat', { message: content });
      setMessages([...messages, response.data]);
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return { messages, isLoading, sendMessage };
}

// Uso en componente
function ChatContainer() {
  const { messages, isLoading, sendMessage } = useChat();
  // ...
}
```

### ✅ Error Boundaries

```tsx
// components/ErrorBoundary.tsx
import { Component, ReactNode } from 'react';

interface Props {
  children: ReactNode;
}

interface State {
  hasError: boolean;
}

export class ErrorBoundary extends Component<Props, State> {
  state = { hasError: false };

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  render() {
    if (this.state.hasError) {
      return <div>Algo salió mal. Por favor recarga la página.</div>;
    }
    return this.props.children;
  }
}
```

---

## 7 — Diseño UI/UX

### 🎨 Principios de Diseño

1. **Claridad:** La UI debe ser intuitiva sin manual
2. **Feedback:** Siempre mostrar loading/success/error states
3. **Consistencia:** Mismos patrones en toda la app
4. **Eficiencia:** Mínimos clics para tareas comunes
5. **Delicia:** Animaciones sutiles que mejoran UX

### 🎨 Paleta de Colores (sugerida)

```css
/* tailwind.config.js */
theme: {
  extend: {
    colors: {
      primary: {
        50: '#eff6ff',
        500: '#3b82f6',
        600: '#2563eb',
        700: '#1d4ed8',
      },
      success: '#10b981',
      warning: '#f59e0b',
      error: '#ef4444',
    }
  }
}
```

### 🎨 Componentes Clave con shadcn/ui

```bash
# Instalar componentes necesarios
npx shadcn-ui@latest add button
npx shadcn-ui@latest add card
npx shadcn-ui@latest add input
npx shadcn-ui@latest add badge
npx shadcn-ui@latest add switch
npx shadcn-ui@latest add progress
npx shadcn-ui@latest add alert
```

### 🎨 Responsive Design

```tsx
// Mobile-first approach
<div className="
  flex flex-col           // Mobile: columna
  md:flex-row             // Tablet+: fila
  gap-4                   // Espaciado consistente
  p-4 md:p-6 lg:p-8       // Padding progresivo
">
  <div className="w-full md:w-2/3">
    {/* Chat */}
  </div>
  <div className="w-full md:w-1/3">
    {/* Timeline */}
  </div>
</div>
```

---

## 8 — Accesibilidad (a11y)

### ♿ Obligatorio

```tsx
// ✅ ARIA labels
<button aria-label="Enviar mensaje">
  <SendIcon />
</button>

// ✅ Roles semánticos
<div role="alert" aria-live="polite">
  {errorMessage}
</div>

// ✅ Focus visible
<input
  className="border rounded focus:ring-2 focus:ring-blue-500 focus:outline-none"
/>

// ✅ Keyboard navigation
<button
  onClick={handleClick}
  onKeyDown={(e) => {
    if (e.key === 'Enter' || e.key === ' ') {
      handleClick();
    }
  }}
>
  Acción
</button>
```

### ♿ Contraste de Colores

- Texto normal: ratio 4.5:1
- Texto grande: ratio 3:1
- Usar herramientas como WebAIM Contrast Checker

---

## 9 — Integración con Backend

### 🔌 Cliente API

```tsx
// services/api.ts
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const api = {
  async post<T>(endpoint: string, data: any): Promise<T> {
    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(data),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.statusText}`);
    }

    return response.json();
  },

  async upload(endpoint: string, file: File): Promise<any> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}${endpoint}`, {
      method: 'POST',
      body: formData,
    });

    return response.json();
  },
};
```

### 🔌 Servicio de Chat

```tsx
// services/chatService.ts
import { api } from './api';

export interface ChatRequest {
  message: string;
  context?: string[];
}

export interface ChatResponse {
  response: string;
  agentSteps?: AgentStep[];
}

export const chatService = {
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return api.post<ChatResponse>('/api/chat', request);
  },
};
```

---

## 10 — Testing Frontend

### 🧪 Setup de Testing

```bash
npm install -D vitest @testing-library/react @testing-library/jest-dom @testing-library/user-event
```

```tsx
// tests/setup.ts
import '@testing-library/jest-dom';

// tests/components/ChatMessage.test.tsx
import { render, screen } from '@testing-library/react';
import { ChatMessage } from '@/components/chat/ChatMessage';

describe('ChatMessage', () => {
  it('renders user message correctly', () => {
    const message = {
      id: '1',
      role: 'user' as const,
      content: 'Hola',
      timestamp: new Date(),
    };

    render(<ChatMessage message={message} />);
    
    expect(screen.getByText('Hola')).toBeInTheDocument();
    expect(screen.getByRole('article')).toHaveClass('message-user');
  });
});
```

### 🧪 Tests Clave

1. **Componentes de UI:** Rendering, props, interacciones
2. **Custom hooks:** Lógica de estado, efectos
3. **Servicios:** Mocks de API calls
4. **Integración:** Flujo completo de enviar mensaje

---

## 11 — Deploy Frontend

### 🚀 Vercel (Recomendado)

```bash
# Instalar Vercel CLI
npm i -g vercel

# Deploy
vercel --prod
```

**Configuración:**

```json
// vercel.json
{
  "framework": "vite",
  "buildCommand": "npm run build",
  "outputDirectory": "dist",
  "env": {
    "VITE_API_URL": "@api-url"
  }
}
```

### 🚀 Variables de Entorno

```bash
# .env.local
VITE_API_URL=https://servibot-backend.onrender.com
VITE_ENABLE_VOICE=true
```

---

## 12 — Output de Copilot Frontend

### Cada vez que generes código frontend, incluye:

1. ✅ **Componente completo** con TypeScript
2. ✅ **Estilos** con Tailwind CSS
3. ✅ **Test** del componente (Vitest)
4. ✅ **Tipos** necesarios (interfaces/types)
5. ✅ **Commit message** (Conventional Commits)
6. ✅ **PR sugerido** con descripción

### Formato de Commit

```
feat(chat): add voice recording component

- Implement VoiceRecorder with MediaRecorder API
- Add visual indicator while recording
- Integrate with Whisper service
- Add unit tests for recording logic

Closes #24
```

---

## 13 — Roadmap Frontend (alineado con roadmap general)

### 🗓️ Semana 0 — Hoy

- [ ] Setup Vite + React + TypeScript
- [ ] Configurar Tailwind CSS
- [ ] Instalar shadcn/ui
- [ ] Estructura de carpetas
- [ ] Layout base (Header + main content)

### 🗓️ Semana 1 — 4 al 11 Dic

- [ ] ChatContainer básico
- [ ] ChatInput con envío de mensajes
- [ ] ChatHistory con scroll automático
- [ ] Integración con endpoint `/api/chat`

### 🗓️ Semana 2 — 12 al 18 Dic

- [ ] AgentTimeline component
- [ ] TaskCard con estados visuales
- [ ] FileUpload con drag & drop
- [ ] Tests de componentes clave

### 🗓️ Semana 3 — 19 al 25 Dic

- [ ] VoiceRecorder implementado
- [ ] Integración Whisper
- [ ] AudioPlayer para ElevenLabs
- [ ] Responsive design completo

### 🗓️ Semana 4 — 26 Dic al 1 Ene

- [ ] SettingsPanel
- [ ] Dark mode (opcional)
- [ ] Pulido de UX
- [ ] Deploy a Vercel

### 🗓️ Semana 5-6 — 2 al 15 Ene

- [ ] Animaciones sutiles
- [ ] Loading states mejorados
- [ ] Error handling UI
- [ ] Accesibilidad completa

### 🗓️ Semana 7-8 — 16 al 27 Ene

- [ ] Testing completo
- [ ] Optimización de performance
- [ ] Documentación componentes
- [ ] Preparación demo final

---

## 14 — Checklist Pre-Commit Frontend

Antes de cada commit, verifica:

- [ ] ✅ TypeScript sin errores (`npm run type-check`)
- [ ] ✅ Build exitoso (`npm run build`)
- [ ] ✅ Tests pasan (`npm run test`)
- [ ] ✅ Linter sin warnings (`npm run lint`)
- [ ] ✅ Componente es responsive
- [ ] ✅ Accesibilidad básica (labels, contrast)
- [ ] ✅ No hay console.logs innecesarios

---

## 15 — Recursos Técnicos Frontend

### Documentación Oficial

- React: https://react.dev/
- TypeScript: https://www.typescriptlang.org/
- Vite: https://vitejs.dev/
- Tailwind CSS: https://tailwindcss.com/
- shadcn/ui: https://ui.shadcn.com/

### Librerías Clave

```json
// package.json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-markdown": "^9.0.0",
    "zustand": "^4.4.7",
    "lucide-react": "^0.300.0",
    "date-fns": "^3.0.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.0",
    "@types/react-dom": "^18.2.0",
    "@vitejs/plugin-react": "^4.2.0",
    "typescript": "^5.3.0",
    "vite": "^5.0.0",
    "tailwindcss": "^3.4.0",
    "vitest": "^1.1.0",
    "@testing-library/react": "^14.1.0",
    "@testing-library/jest-dom": "^6.1.0"
  }
}
```

---

## 16 — Mantra Frontend Copilot

> **"UI clara, código limpio, TypeScript estricto.  
> Primero funcionalidad, luego belleza.  
> Cada componente debe demostrar ingeniería frontend moderna."**

---

**Fin de instrucciones-frontend.md**