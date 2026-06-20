/* =============================================================
   ESTIA — AI Hotel Concierge
   Frontend chat logic
   ============================================================= */

const API = '/api/v1';

// ── State ──────────────────────────────────────────────────────
let conversationId = null;
let currentMode    = 'text';   // 'text' | 'voice' | 'image'
let language       = null;     // null = auto-detect
let propertyId     = null;
let isLoading      = false;
let mediaRecorder  = null;
let audioChunks    = [];
let selectedImage  = null;     // { file, dataUrl }

// ── DOM refs ───────────────────────────────────────────────────
const messagesEl    = document.getElementById('messages');
const textInput     = document.getElementById('textInput');
const sendBtn       = document.getElementById('sendBtn');
const micBtn        = document.getElementById('micBtn');
const voiceLabel    = document.getElementById('voiceLabel');
const voiceWave     = document.getElementById('voiceWave');
const audioFileInput = document.getElementById('audioFileInput');
const imageFileInput = document.getElementById('imageFileInput');
const imagePreview  = document.getElementById('imagePreview');
const imageDropLabel = document.getElementById('imageDropLabel');
const imageDropZone = document.getElementById('imageDropZone');
const imageQuestion = document.getElementById('imageQuestion');
const imageSendBtn  = document.getElementById('imageSendBtn');
const propertySelect = document.getElementById('propertySelect');
const newChatBtn    = document.getElementById('newChatBtn');
const headerTitle   = document.getElementById('headerTitle');
const headerMeta    = document.getElementById('headerMeta');

// ── Mode switching ─────────────────────────────────────────────
document.querySelectorAll('.nav-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    setMode(btn.dataset.mode);
  });
});

function setMode(mode) {
  currentMode = mode;

  document.querySelectorAll('.nav-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.mode === mode)
  );

  document.getElementById('textPanel').classList.toggle('hidden',  mode !== 'text');
  document.getElementById('voicePanel').classList.toggle('hidden', mode !== 'voice');
  document.getElementById('imagePanel').classList.toggle('hidden', mode !== 'image');

  const titles = { text: 'Text Concierge', voice: 'Voice Concierge', image: 'Image Concierge' };
  const metas  = { text: 'GPT-4o · RAG enabled', voice: 'Whisper STT · TTS enabled', image: 'GPT-4o Vision · RAG enabled' };
  headerTitle.textContent = titles[mode];
  headerMeta.textContent  = metas[mode];
}

// ── Language toggle ────────────────────────────────────────────
document.querySelectorAll('.lang-btn').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    language = btn.dataset.lang === 'en' ? null : btn.dataset.lang;
  });
});

// ── Property select ────────────────────────────────────────────
propertySelect.addEventListener('change', () => {
  propertyId = propertySelect.value || null;
});

// ── New conversation ───────────────────────────────────────────
newChatBtn.addEventListener('click', () => {
  conversationId = null;
  selectedImage  = null;
  messagesEl.innerHTML = '';
  messagesEl.appendChild(buildWelcome());
});

function buildWelcome() {
  const div = document.createElement('div');
  div.className = 'welcome';
  div.innerHTML = `
    <div class="welcome__icon">🏨</div>
    <h1 class="welcome__title">Welcome to ESTIA</h1>
    <p class="welcome__subtitle">
      Your personal AI concierge for the Elounda Collection.<br/>
      Ask me anything about our hotels, restaurants, spa, or activities.
    </p>
    <div class="welcome__chips">
      <button class="chip" data-prompt="What restaurants do you have?">Restaurants</button>
      <button class="chip" data-prompt="What time does the spa open?">Spa hours</button>
      <button class="chip" data-prompt="Can I arrange a yacht charter?">Yacht charter</button>
      <button class="chip" data-prompt="Tell me about the kids club">Kids club</button>
      <button class="chip" data-prompt="How do I get from Heraklion airport?">Airport transfer</button>
      <button class="chip" data-prompt="Τι δραστηριότητες έχετε;">Δραστηριότητες</button>
    </div>`;
  attachChips(div);
  return div;
}

// ── Chip clicks (welcome screen) ───────────────────────────────
function attachChips(container) {
  container.querySelectorAll('.chip').forEach(chip => {
    chip.addEventListener('click', () => {
      setMode('text');
      textInput.value = chip.dataset.prompt;
      sendTextMessage();
    });
  });
}

// Chips in initial HTML
attachChips(document);

// ── Text chat ──────────────────────────────────────────────────
sendBtn.addEventListener('click', sendTextMessage);

textInput.addEventListener('keydown', e => {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendTextMessage();
  }
});

textInput.addEventListener('input', () => {
  textInput.style.height = 'auto';
  textInput.style.height = Math.min(textInput.scrollHeight, 140) + 'px';
});

async function sendTextMessage() {
  const text = textInput.value.trim();
  if (!text || isLoading) return;

  textInput.value = '';
  textInput.style.height = 'auto';
  clearWelcome();
  appendMessage('user', text);
  const typing = appendTyping();
  setLoading(true);

  try {
    const body = { message: text };
    if (conversationId) body.conversation_id = conversationId;
    if (language)       body.language = language;
    if (propertyId)     body.property_id = propertyId;

    const res  = await fetch(`${API}/chat`, {
      method:  'POST',
      headers: { 'Content-Type': 'application/json' },
      body:    JSON.stringify(body),
    });

    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Request failed');

    conversationId = data.conversation_id;
    typing.remove();
    appendMessage('assistant', data.reply, `${data.language_detected.toUpperCase()} · ${data.tokens_used} tokens`);
  } catch (err) {
    typing.remove();
    showToast(err.message);
  } finally {
    setLoading(false);
  }
}

// ── Voice recording ────────────────────────────────────────────
micBtn.addEventListener('mousedown', startRecording);
micBtn.addEventListener('touchstart', e => { e.preventDefault(); startRecording(); });
micBtn.addEventListener('mouseup',   stopRecording);
micBtn.addEventListener('touchend',  stopRecording);
micBtn.addEventListener('mouseleave', () => { if (mediaRecorder?.state === 'recording') stopRecording(); });

async function startRecording() {
  if (isLoading) return;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    audioChunks = [];
    mediaRecorder = new MediaRecorder(stream);
    mediaRecorder.ondataavailable = e => audioChunks.push(e.data);
    mediaRecorder.onstop = () => {
      stream.getTracks().forEach(t => t.stop());
      const blob = new Blob(audioChunks, { type: 'audio/webm' });
      sendAudio(blob, 'recording.webm');
    };
    mediaRecorder.start();
    micBtn.classList.add('recording');
    voiceLabel.textContent = 'Recording… release to send';
    voiceWave.classList.remove('hidden');
  } catch {
    showToast('Microphone access denied');
  }
}

function stopRecording() {
  if (mediaRecorder?.state === 'recording') {
    mediaRecorder.stop();
    micBtn.classList.remove('recording');
    voiceLabel.textContent = 'Hold to record';
    voiceWave.classList.add('hidden');
  }
}

// Audio file upload
audioFileInput.addEventListener('change', () => {
  if (audioFileInput.files[0]) sendAudio(audioFileInput.files[0], audioFileInput.files[0].name);
});

async function sendAudio(blob, filename) {
  clearWelcome();
  appendMessage('user', `🎙️ Voice message`);
  const typing = appendTyping();
  setLoading(true);

  try {
    const fd = new FormData();
    fd.append('audio', blob, filename);
    if (conversationId) fd.append('conversation_id', conversationId);
    if (propertyId)     fd.append('property_id', propertyId);
    fd.append('tts_enabled', 'true');

    const res  = await fetch(`${API}/voice/chat`, { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Voice request failed');

    conversationId = data.conversation_id;
    typing.remove();

    appendMessage('user', `"${data.transcript}"`, 'Transcribed');
    appendMessage('assistant', data.reply, `${data.language_detected.toUpperCase()} · ${data.tokens_used} tokens`);

    if (data.audio_available) playTTS(data.reply, data.language_detected);
  } catch (err) {
    typing.remove();
    showToast(err.message);
  } finally {
    setLoading(false);
  }
}

async function playTTS(text, lang) {
  try {
    const fd = new FormData();
    fd.append('text', text);
    fd.append('language', lang || 'en');
    const res = await fetch(`${API}/voice/speak`, { method: 'POST', body: fd });
    if (!res.ok) return;
    const blob = await res.blob();
    const url  = URL.createObjectURL(blob);
    const audio = new Audio(url);
    audio.play();
    audio.onended = () => URL.revokeObjectURL(url);
  } catch { /* TTS failure is non-fatal */ }
}

// ── Image chat ─────────────────────────────────────────────────
imageFileInput.addEventListener('change', () => loadImageFile(imageFileInput.files[0]));

imageDropZone.addEventListener('dragover', e => {
  e.preventDefault();
  imageDropZone.classList.add('drag-over');
});
imageDropZone.addEventListener('dragleave', () => imageDropZone.classList.remove('drag-over'));
imageDropZone.addEventListener('drop', e => {
  e.preventDefault();
  imageDropZone.classList.remove('drag-over');
  const file = e.dataTransfer.files[0];
  if (file?.type.startsWith('image/')) loadImageFile(file);
});

function loadImageFile(file) {
  if (!file) return;
  const reader = new FileReader();
  reader.onload = e => {
    selectedImage = { file, dataUrl: e.target.result };
    imagePreview.src = e.target.result;
    imagePreview.classList.remove('hidden');
    imageDropLabel.classList.add('hidden');
  };
  reader.readAsDataURL(file);
}

imageSendBtn.addEventListener('click', sendImageMessage);
imageQuestion.addEventListener('keydown', e => {
  if (e.key === 'Enter') sendImageMessage();
});

async function sendImageMessage() {
  if (!selectedImage || isLoading) return;
  const question = imageQuestion.value.trim() || 'What can you tell me about this?';
  imageQuestion.value = '';

  clearWelcome();
  appendMessage('user', question, null, selectedImage.dataUrl);
  const typing = appendTyping();
  setLoading(true);

  try {
    const fd = new FormData();
    fd.append('image', selectedImage.file, selectedImage.file.name);
    fd.append('question', question);
    if (conversationId) fd.append('conversation_id', conversationId);
    if (propertyId)     fd.append('property_id', propertyId);
    if (language)       fd.append('language', language);

    const res  = await fetch(`${API}/image/chat`, { method: 'POST', body: fd });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || 'Image request failed');

    conversationId = data.conversation_id;
    typing.remove();
    appendMessage('assistant', data.reply, `${data.language_detected.toUpperCase()} · ${data.tokens_used} tokens`);

    // Reset image after sending
    selectedImage = null;
    imagePreview.classList.add('hidden');
    imagePreview.src = '';
    imageDropLabel.classList.remove('hidden');
  } catch (err) {
    typing.remove();
    showToast(err.message);
  } finally {
    setLoading(false);
  }
}

// ── DOM helpers ────────────────────────────────────────────────
function clearWelcome() {
  const welcome = messagesEl.querySelector('.welcome');
  if (welcome) welcome.remove();
}

function appendMessage(role, text, meta = null, imageDataUrl = null) {
  const wrap = document.createElement('div');
  wrap.className = `message message--${role}`;

  if (imageDataUrl) {
    const img = document.createElement('img');
    img.className = 'message__image';
    img.src = imageDataUrl;
    wrap.appendChild(img);
  }

  const bubble = document.createElement('div');
  bubble.className = 'message__bubble';
  bubble.textContent = text;
  wrap.appendChild(bubble);

  if (meta) {
    const metaEl = document.createElement('div');
    metaEl.className = 'message__meta';
    metaEl.textContent = meta;
    wrap.appendChild(metaEl);
  }

  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function appendTyping() {
  const wrap = document.createElement('div');
  wrap.className = 'message message--assistant';
  wrap.innerHTML = `
    <div class="typing-indicator">
      <span></span><span></span><span></span>
    </div>`;
  messagesEl.appendChild(wrap);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  return wrap;
}

function setLoading(state) {
  isLoading = state;
  sendBtn.disabled     = state;
  imageSendBtn.disabled = state;
  micBtn.style.opacity = state ? '.4' : '1';
  micBtn.style.pointerEvents = state ? 'none' : '';
}

function showToast(message) {
  const existing = document.querySelector('.toast');
  if (existing) existing.remove();
  const toast = document.createElement('div');
  toast.className = 'toast';
  toast.textContent = message;
  document.body.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
