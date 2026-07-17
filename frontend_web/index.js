/* SoulBook Web Frontend - App Logic with Auth0 Integration */

// Dynamically adapt backend URL depending on environment
const isLocal = window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1';
const API_BASE_URL = isLocal 
  ? 'http://127.0.0.1:8000/api/v1' 
  : `https://${window.location.hostname.replace('-frontend', '-backend')}/api/v1`;

const WS_BASE_URL = isLocal 
  ? 'ws://127.0.0.1:8000/ws/v1' 
  : `wss://${window.location.hostname.replace('-frontend', '-backend')}/ws/v1`;

const DEFAULT_USER_ID = '319c5c11-9a74-4b53-a5c9-59eb4df8f4a1';


// Auth0 Configuration
// Set to your real Auth0 values. If left as 'your-client-id-here', local mock developer auth is active.
const AUTH0_DOMAIN = 'dev-lifemovie.us.auth0.com';
const AUTH0_CLIENT_ID = 'your-client-id-here';
const AUTH0_AUDIENCE = 'http://127.0.0.1:8000/api';

let auth0Client = null;
let useMockAuth = true;

// App State
const state = {
  isLoggedIn: false,
  activeTab: 'home',
  diaries: [],
  characters: [],
  movies: [],
  jobs: [],
  ws: null,
  progress: {}, // Stores WebSocket progress messages by movie title
  user: null
};

// Initialize App
document.addEventListener('DOMContentLoaded', () => {
  initAuth().then(() => {
    initLoginHandler();
    initNavigation();
    initForms();
    initModal();
    updateMockStats();
  });
});

// Mock counter for dashboard header
function updateMockStats() {
  // Can be hardcoded or dynamically computed
}

// Auth0 SDK Initialization
async function initAuth() {
  if (AUTH0_CLIENT_ID === 'your-client-id-here') {
    useMockAuth = true;
    console.log("Auth0 running in Local Mock Mode. Add real AUTH0_CLIENT_ID in index.js to configure Auth0.");
    
    // Check if mock callback redirect happened
    if (window.location.search.includes('code=') && window.location.search.includes('state=')) {
      state.isLoggedIn = true;
      history.replaceState({}, document.title, window.location.pathname);
      const mockUser = {
        name: "Siddu",
        email: "siddu@example.com",
        picture: "https://picsum.photos/100/100?random=99"
      };
      state.user = mockUser;
      updateUserProfileUI(mockUser);
      onUserAuthenticated();
      showToast("Logged in with mock developer profile", "success");
    }
    return;
  }
  
  try {
    auth0Client = await createAuth0Client({
      domain: AUTH0_DOMAIN,
      clientId: AUTH0_CLIENT_ID,
      authorizationParams: {
        redirect_uri: window.location.origin + window.location.pathname,
        audience: AUTH0_AUDIENCE
      }
    });
    
    useMockAuth = false;
    
    // Process Auth0 callback if redirected
    const query = window.location.search;
    if (query.includes("code=") && query.includes("state=")) {
      await auth0Client.handleRedirectCallback();
      history.replaceState({}, document.title, window.location.pathname);
    }
    
    const authenticated = await auth0Client.isAuthenticated();
    if (authenticated) {
      state.isLoggedIn = true;
      const user = await auth0Client.getUser();
      state.user = user;
      updateUserProfileUI(user);
      onUserAuthenticated();
    }
  } catch (err) {
    console.warn("Auth0 initialization failed. Running in fallback Local Mock Mode.", err);
    useMockAuth = true;
  }
}

// Generate Auth Headers for Fetch Requests
async function getAuthHeaders(isPost = false) {
  const headers = {};
  if (isPost) {
    headers['Content-Type'] = 'application/json';
  }
  
  if (!useMockAuth && auth0Client) {
    try {
      const token = await auth0Client.getTokenSilently();
      headers['Authorization'] = `Bearer ${token}`;
    } catch (err) {
      console.warn("Could not retrieve Auth0 token silently:", err);
    }
  } else {
    // Inject mock token for developer preview
    headers['Authorization'] = 'Bearer mock-developer-token';
  }
  return headers;
}

// Update User Profile Display in UI
function updateUserProfileUI(user) {
  const nameEl = document.querySelector('.user-name');
  const picEl = document.querySelector('.user-profile-badge img');
  const greetEl = document.querySelector('.greeting-header h1');
  
  if (nameEl) nameEl.textContent = user.name || user.email;
  if (picEl && user.picture) picEl.src = user.picture;
  if (greetEl) {
    const displayName = user.given_name || user.name || 'Siddu';
    greetEl.textContent = `Good Evening, ${displayName} 👋`;
  }
}

// Handler when user successfully logs in
function onUserAuthenticated() {
  const landingSec = document.getElementById('landing-page');
  const dashSec = document.getElementById('dashboard-page');
  
  landingSec.classList.remove('active');
  dashSec.classList.add('active');
  
  // Load data and start websocket listener
  loadAllData();
  connectWebSocket();
  window.scrollTo(0, 0);
}

// Login triggers handler
function initLoginHandler() {
  const loginTriggers = document.querySelectorAll('.btn-login-trigger');
  const logoutTrigger = document.querySelector('.btn-logout');
  
  loginTriggers.forEach(btn => {
    btn.addEventListener('click', async () => {
      if (useMockAuth) {
        state.isLoggedIn = true;
        const mockUser = {
          name: "Siddu",
          email: "siddu@example.com",
          picture: "https://picsum.photos/100/100?random=99"
        };
        state.user = mockUser;
        updateUserProfileUI(mockUser);
        onUserAuthenticated();
        showToast("Logged in successfully (Mock Auth)", "success");
      } else {
        try {
          await auth0Client.loginWithRedirect();
        } catch (err) {
          showToast("Auth0 redirect failed. Verify client credentials.", "error");
        }
      }
    });
  });
  
  if (logoutTrigger) {
    logoutTrigger.addEventListener('click', async () => {
      state.isLoggedIn = false;
      const landingSec = document.getElementById('landing-page');
      const dashSec = document.getElementById('dashboard-page');
      dashSec.classList.remove('active');
      landingSec.classList.add('active');
      
      if (state.ws) {
        state.ws.close();
      }
      
      window.scrollTo(0, 0);
      
      if (!useMockAuth && auth0Client) {
        auth0Client.logout({
          logoutParams: {
            returnTo: window.location.origin + window.location.pathname
          }
        });
      } else {
        showToast("Logged out successfully", "success");
      }
    });
  }
}

// Navigation between Sidebar & Mobile subtabs
function initNavigation() {
  const sidebarBtns = document.querySelectorAll('.sidebar-nav .nav-btn');
  const mobileBtns = document.querySelectorAll('.app-mobile-nav .mobile-nav-btn');
  const subtabs = document.querySelectorAll('.dashboard-subtab');
  
  function switchSubtab(targetTab) {
    // Update active class on sidebar buttons
    sidebarBtns.forEach(btn => {
      btn.classList.remove('active');
      if (btn.getAttribute('data-target') === targetTab) {
        btn.classList.add('active');
      }
    });
    
    // Update active class on mobile navigation buttons
    mobileBtns.forEach(btn => {
      btn.classList.remove('active');
      if (btn.getAttribute('data-target') === targetTab) {
        btn.classList.add('active');
      }
    });
    
    // Show correct subtab panel
    subtabs.forEach(sub => {
      sub.classList.remove('active');
      if (sub.id === `sub-${targetTab}`) {
        sub.classList.add('active');
      }
    });
    
    state.activeTab = targetTab;
    
    // Lazy loads based on tab
    if (targetTab === 'timeline') loadDiaries();
    if (targetTab === 'studio') loadMovies();
    if (targetTab === 'characters') loadCharacters();
    if (targetTab === 'home') loadAllData();
  }
  
  // Attach click listeners
  sidebarBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-target');
      switchSubtab(target);
    });
  });
  
  mobileBtns.forEach(btn => {
    btn.addEventListener('click', () => {
      const target = btn.getAttribute('data-target');
      if (target) {
        switchSubtab(target);
      }
    });
  });

  // Greet CTA triggers: Quick buttons trigger tab switching
  const createTriggers = document.querySelectorAll('.btn-create-trigger');
  createTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      switchSubtab('create');
    });
  });

  const studioTriggers = document.querySelectorAll('.btn-studio-trigger');
  studioTriggers.forEach(btn => {
    btn.addEventListener('click', (e) => {
      e.stopPropagation();
      switchSubtab('studio');
    });
  });
}

// Create Memory Tab selection inner logic
const createTabBtns = document.querySelectorAll('.create-tab-btn');
createTabBtns.forEach(btn => {
  btn.addEventListener('click', () => {
    createTabBtns.forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    
    const mode = btn.getAttribute('data-mode');
    const contentTextarea = document.getElementById('diary-content');
    if (contentTextarea) {
      if (mode === 'speak') {
        contentTextarea.placeholder = "Recording voice... Click Save when you are finished talking to transcribe.";
        contentTextarea.value = "We had a family picnic at the beach in Goa today. The kids built sandcastles, we ate fresh mangoes, and Dad played guitar while the sun went down.";
      } else if (mode === 'upload') {
        // Trigger file select
        const fileInput = document.getElementById('diary-media-file');
        if (fileInput) fileInput.click();
      } else if (mode === 'import') {
        contentTextarea.placeholder = "Import logs from Instagram, WhatsApp, or Apple Photos...";
        contentTextarea.value = "Imported WhatsApp chat logs from July 14, 2026: 'What a perfect day in Goa! Family picnic on the beach was amazing. Best sunset ever!'";
      } else {
        contentTextarea.placeholder = "Tell me about your day...";
        contentTextarea.value = "";
      }
    }
  });
});

// Setup File Upload Event Listener
document.addEventListener('DOMContentLoaded', () => {
  const mediaFileInput = document.getElementById('diary-media-file');
  if (mediaFileInput) {
    mediaFileInput.addEventListener('change', async (e) => {
      const file = e.target.files[0];
      if (!file) return;
      
      const contentTextarea = document.getElementById('diary-content');
      if (contentTextarea) {
        contentTextarea.placeholder = "Uploading your media file...";
        contentTextarea.value = `[Uploading: ${file.name}...]`;
      }
      
      const formData = new FormData();
      formData.append('file', file);
      
      try {
        const authHeaders = await getAuthHeaders(false); // get auth headers without JSON Content-Type
        
        const response = await fetch(`${API_BASE_URL}/diaries/upload`, {
          method: 'POST',
          headers: authHeaders,
          body: formData
        });
        
        if (!response.ok) throw new Error('Upload failed');
        const data = await response.json();
        
        showToast(`Media "${file.name}" uploaded successfully!`, 'success');
        if (contentTextarea) {
          contentTextarea.value = `I captured this beautiful memory. \n\n[Uploaded Media: ${data.url}]`;
        }
      } catch (err) {
        showToast(`Media upload failed: ${err.message}`, 'error');
        if (contentTextarea) {
          contentTextarea.value = '';
          contentTextarea.placeholder = "Tell me about your day...";
        }
      }
    });
  }
});

// Form Handlers
function initForms() {
  // Create Diary Form
  const formDiary = document.getElementById('form-create-diary');
  if (formDiary) {
    formDiary.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const title = document.getElementById('diary-title').value;
      const content = document.getElementById('diary-content').value;
      const mood = document.getElementById('diary-mood').value;
      const moodIntensity = parseFloat(document.getElementById('diary-mood-intensity').value) / 10.0;
      const location = document.getElementById('diary-location').value || null;
      const people = document.getElementById('diary-people').value || '';
      const lang = document.getElementById('diary-lang').value || 'en';
      
      const weather = document.getElementById('diary-weather').value || null;
      const privacy = document.getElementById('diary-privacy').value;
      const isDraft = document.getElementById('diary-draft').value === 'true';

      // Assemble content, embedding people/language context so the backend is enriched
      let finalContent = content;
      if (people) finalContent += `\n\n[People present: ${people}]`;
      if (lang) finalContent += `\n[Narrated Language: ${lang}]`;
      
      const payload = {
        user_id: DEFAULT_USER_ID,
        title,
        content_raw: finalContent,
        mood,
        mood_intensity: moodIntensity,
        location_name: location,
        weather_condition: weather,
        privacy_level: privacy,
        is_draft: isDraft
      };
      
      try {
        const response = await fetch(`${API_BASE_URL}/diaries/`, {
          method: 'POST',
          headers: await getAuthHeaders(true),
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to save memory');
        
        showToast('Memory entry saved successfully!', 'success');
        formDiary.reset();
        
        // Return Create tab to "write" default text
        const firstTab = document.querySelector('.create-tab-btn[data-mode="write"]');
        if (firstTab) firstTab.click();
        
        // Go back to timeline to see it
        const timelineBtn = document.querySelector('.sidebar-nav [data-target="timeline"]');
        if (timelineBtn) timelineBtn.click();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
  
  // Create Character Form
  const formChar = document.getElementById('form-create-character');
  if (formChar) {
    formChar.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const name = document.getElementById('char-name').value;
      const relationship = document.getElementById('char-relationship').value;
      const gender = document.getElementById('char-gender').value;
      const hairPrompt = document.getElementById('char-hair-prompt').value || null;
      const personality = document.getElementById('char-personality').value || null;
      
      const payload = {
        user_id: DEFAULT_USER_ID,
        name,
        relationship_type: relationship,
        gender,
        hair_style_prompt: hairPrompt,
        personality_prompt: personality
      };
      
      try {
        const response = await fetch(`${API_BASE_URL}/characters/`, {
          method: 'POST',
          headers: await getAuthHeaders(true),
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to save character');
        
        showToast('Character registered successfully!', 'success');
        formChar.reset();
        loadCharacters();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
  
  // Generate Movie Form
  const formMovie = document.getElementById('form-generate-movie');
  if (formMovie) {
    formMovie.addEventListener('submit', async (e) => {
      e.preventDefault();
      
      const title = document.getElementById('movie-title').value;
      const preset = document.getElementById('movie-preset').value;
      const summary = document.getElementById('movie-summary').value || null;
      
      const payload = {
        user_id: DEFAULT_USER_ID,
        title,
        style_preset: preset,
        summary
      };
      
      try {
        const response = await fetch(`${API_BASE_URL}/movies/`, {
          method: 'POST',
          headers: await getAuthHeaders(true),
          body: JSON.stringify(payload)
        });
        
        if (!response.ok) throw new Error('Failed to create movie job');
        const movie = await response.json();
        
        showToast(`Movie job "${title}" created. Initializing rendering...`, 'success');
        formMovie.reset();
        
        await triggerMovieRender(movie.id);
        loadMovies();
      } catch (err) {
        showToast(err.message, 'error');
      }
    });
  }
}

// Trigger Render Call
async function triggerMovieRender(movieId) {
  try {
    const response = await fetch(`${API_BASE_URL}/movies/${movieId}/trigger-render`, {
      method: 'POST',
      headers: await getAuthHeaders(true)
    });
    if (!response.ok) throw new Error('Failed to trigger rendering engine');
    const updatedMovie = await response.json();
    showToast(`Stitching engine active for movie. Status: ${updatedMovie.status}`, 'success');
  } catch (err) {
    console.error(err);
  }
}

// Load Data Helpers
async function loadAllData() {
  await Promise.all([
    loadDiaries(),
    loadCharacters(),
    loadMovies()
  ]);
  renderHomeDashboard();
}

async function loadDiaries() {
  try {
    const response = await fetch(`${API_BASE_URL}/diaries/`, {
      headers: await getAuthHeaders(false)
    });
    if (!response.ok) throw new Error('Could not fetch diaries');
    state.diaries = await response.json();
    renderTimeline();
  } catch (err) {
    console.warn('Fallback to mock diaries', err);
    state.diaries = [
      { id: '1', title: 'Trip to Alps', content_raw: 'Had an amazing hike today. The weather was cool, around 18°C. We climbed up the main trail and saw beautiful snowy peaks.', captured_at: new Date().toISOString(), mood: 'joyful', location_name: 'Swiss Alps', weather_condition: 'Sunny' },
      { id: '2', title: 'Leo\'s First Step', content_raw: 'Leo stood up on his own and walked three steps to Sarah. We were both screaming with joy! Videotaped the whole thing.', captured_at: new Date(Date.now() - 86400000).toISOString(), mood: 'excited', location_name: 'Living Room' }
    ];
    renderTimeline();
  }
}

async function loadCharacters() {
  try {
    const response = await fetch(`${API_BASE_URL}/characters/`, {
      headers: await getAuthHeaders(false)
    });
    if (!response.ok) throw new Error('Could not fetch characters');
    state.characters = await response.json();
    renderCharactersList();
  } catch (err) {
    console.warn('Fallback to mock characters', err);
    state.characters = [
      { id: '1', name: 'Sarah Smith', relationship_type: 'Wife', gender: 'female' },
      { id: '2', name: 'Leo Smith', relationship_type: 'Son', gender: 'male' }
    ];
    renderCharactersList();
  }
}

async function loadMovies() {
  try {
    const response = await fetch(`${API_BASE_URL}/movies/`, {
      headers: await getAuthHeaders(false)
    });
    if (!response.ok) throw new Error('Could not fetch movies');
    state.movies = await response.json();
    renderJobsList();
  } catch (err) {
    console.warn('Fallback to mock movies', err);
    state.movies = [
      { id: 'm1', title: 'Summer picnic', status: 'completed', rendered_video_url: '#' },
      { id: 'm2', title: 'Rainy morning', status: 'rendering', rendered_video_url: null }
    ];
    renderJobsList();
  }
}

// Render Functions

// Helper to determine WebSocket progress stage (checked, active, pending)
function getProgressStages(title, status) {
  const message = state.progress[title] || '';
  
  let stages = {
    analysis: 'pending',
    planning: 'pending',
    images: 'pending',
    narration: 'pending',
    music: 'pending',
    rendering: 'pending'
  };
  
  if (status === 'completed') {
    stages = {
      analysis: 'checked',
      planning: 'checked',
      images: 'checked',
      narration: 'checked',
      music: 'checked',
      rendering: 'checked'
    };
  } else if (status === 'rendering') {
    stages.analysis = 'checked';
    stages.planning = 'checked';
    stages.images = 'active'; // Default active stage
    
    if (message.includes('splitting') || message.includes('Gathering')) {
      stages.analysis = 'active';
      stages.planning = 'pending';
      stages.images = 'pending';
    } else if (message.includes('scene')) {
      stages.images = 'active';
    } else if (message.includes('Encoding video clip')) {
      stages.images = 'checked';
      stages.narration = 'active';
    } else if (message.includes('Concatenating')) {
      stages.images = 'checked';
      stages.narration = 'checked';
      stages.music = 'checked';
      stages.rendering = 'active';
    }
  }
  
  return stages;
}

// Renders Netflix/Disney+ style streaming layout grouped by Year/Month
function renderTimeline() {
  const container = document.getElementById('timeline-list-container');
  if (!container) return;
  
  if (state.diaries.length === 0) {
    container.innerHTML = `
      <div class="loading-state">
        <i data-lucide="calendar-x" style="width: 48px; height: 48px; color: var(--color-accent-purple); margin-bottom: 12px;"></i>
        <p>No memories logged yet. Click "Create New" to save your first memory!</p>
      </div>
    `;
    lucide.createIcons();
    return;
  }
  
  // Group diaries by Year and Month
  const sorted = [...state.diaries].sort((a, b) => new Date(b.captured_at) - new Date(a.captured_at));
  
  const groups = {};
  sorted.forEach(diary => {
    const d = new Date(diary.captured_at);
    const year = d.getFullYear();
    const month = d.toLocaleString('en-US', { month: 'long' });
    
    if (!groups[year]) groups[year] = {};
    if (!groups[year][month]) groups[year][month] = [];
    groups[year][month].push(diary);
  });

  let htmlContent = '';
  for (const year in groups) {
    htmlContent += `
      <div class="timeline-year-group">
        <h2 style="font-family: var(--font-heading); font-size: 1.8rem; margin-bottom: 20px; font-weight: 800;">${year}</h2>
    `;
    
    for (const month in groups[year]) {
      htmlContent += `
        <div class="timeline-group" style="margin-bottom: 30px;">
          <h3 class="timeline-group-title">${month}</h3>
          <div class="timeline-cards-row">
      `;
      
      groups[year][month].forEach(diary => {
        const dateStr = new Date(diary.captured_at).toLocaleDateString('en-US', {
          weekday: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit'
        });
        
        htmlContent += `
          <div class="timeline-card">
            <div class="timeline-meta">
              <span>${dateStr}</span>
              ${diary.is_draft ? '<span class="badge" style="background:var(--color-accent-purple)">DRAFT</span>' : ''}
            </div>
            <h3 class="timeline-title">${escapeHtml(diary.title)}</h3>
            <p class="timeline-content">${escapeHtml(diary.content_raw || '')}</p>
            <div class="timeline-tags">
              ${diary.mood ? `<span class="tag-mood">${diary.mood}</span>` : ''}
              ${diary.location_name ? `<span class="tag-loc"><i data-lucide="map-pin" style="width:10px;height:10px;display:inline;margin-right:2px;"></i> ${escapeHtml(diary.location_name)}</span>` : ''}
            </div>
          </div>
        `;
      });
      
      htmlContent += `
          </div>
        </div>
      `;
    }
    
    htmlContent += `</div>`;
  }
  
  container.innerHTML = htmlContent;
  lucide.createIcons();
}

// Renders characters as floating profiles matching Disney/Disney+ design
function renderCharactersList() {
  const container = document.getElementById('studio-characters-list');
  if (!container) return;
  
  if (state.characters.length === 0) {
    container.innerHTML = '<div class="no-jobs w-100">No characters registered yet. Add one on the left!</div>';
    return;
  }
  
  container.innerHTML = state.characters.map(char => {
    let emoji = '👨';
    if (char.relationship_type.toLowerCase().includes('wife') || char.relationship_type.toLowerCase().includes('mother') || char.gender === 'female') {
      emoji = '👩';
    } else if (char.relationship_type.toLowerCase().includes('son') || char.relationship_type.toLowerCase().includes('brother') || char.relationship_type.toLowerCase().includes('kid')) {
      emoji = '👦';
    } else if (char.relationship_type.toLowerCase().includes('dog') || char.relationship_type.toLowerCase().includes('pet')) {
      emoji = '🐶';
    } else if (char.relationship_type.toLowerCase().includes('grandma') || char.relationship_type.toLowerCase().includes('grandmother')) {
      emoji = '👵';
    } else if (char.relationship_type.toLowerCase().includes('grandpa') || char.relationship_type.toLowerCase().includes('grandfather')) {
      emoji = '👴';
    }
    
    return `
      <div class="character-bubble">
        <div style="font-size: 2.2rem; margin-bottom: 8px;">${emoji}</div>
        <div class="character-name">${escapeHtml(char.name)}</div>
        <div class="character-rel" style="margin-bottom: 10px;">${escapeHtml(char.relationship_type)}</div>
        <div style="font-size: 0.75rem; color: var(--color-text-muted); margin-bottom: 12px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; height: 30px;">
          ${escapeHtml(char.personality_prompt || 'Consistent memory avatar')}
        </div>
        <button class="btn btn-secondary" style="padding: 6px 14px; font-size: 0.78rem; border-radius: 8px;">Edit</button>
      </div>
    `;
  }).join('');
}

// Renders active rendering jobs showing a cinematic progress timeline
function renderJobsList() {
  const container = document.getElementById('studio-jobs-list');
  if (!container) return;
  
  const activeJobs = state.movies;
  
  if (activeJobs.length === 0) {
    container.innerHTML = '<div class="no-jobs">No rendering jobs. Start compiling a movie to see progress here.</div>';
    return;
  }
  
  container.innerHTML = activeJobs.map(job => {
    const isRendering = job.status === 'rendering';
    
    if (isRendering) {
      const stages = getProgressStages(job.title, job.status);
      const stageIcon = (st) => st === 'checked' ? 'check' : (st === 'active' ? 'loader-2' : 'clock');
      const stageClass = (st) => st === 'checked' ? 'completed' : (st === 'active' ? 'active' : 'pending');
      const stageSpin = (st) => st === 'active' ? 'spin' : '';
      
      return `
        <div class="card continue-card" style="background-color: rgba(139, 92, 246, 0.04); border-color: rgba(139, 92, 246, 0.2); padding: 20px; width: 100%;">
          <div style="display: flex; justify-content: space-between; margin-bottom: 16px;">
            <h4 style="font-family: var(--font-heading); font-size: 1.1rem; font-weight: 700;">${escapeHtml(job.title)}</h4>
            <span class="job-status status-rendering"><i data-lucide="loader-2" class="spin" style="width: 12px; height: 12px; display: inline-block; vertical-align: middle; margin-right: 4px;"></i> STITCHING...</span>
          </div>
          
          <div class="progress-timeline">
            <div class="timeline-step ${stageClass(stages.analysis)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.analysis)}" class="${stageSpin(stages.analysis)}" style="width:10px;height:10px;"></i></span>
              <span>Story Analysis</span>
            </div>
            <div class="timeline-step ${stageClass(stages.planning)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.planning)}" class="${stageSpin(stages.planning)}" style="width:10px;height:10px;"></i></span>
              <span>Scene Planning</span>
            </div>
            <div class="timeline-step ${stageClass(stages.images)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.images)}" class="${stageSpin(stages.images)}" style="width:10px;height:10px;"></i></span>
              <span>Generating Images</span>
            </div>
            <div class="timeline-step ${stageClass(stages.narration)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.narration)}" class="${stageSpin(stages.narration)}" style="width:10px;height:10px;"></i></span>
              <span>Narration Voiceover</span>
            </div>
            <div class="timeline-step ${stageClass(stages.music)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.music)}" class="${stageSpin(stages.music)}" style="width:10px;height:10px;"></i></span>
              <span>Music & SFX Stitching</span>
            </div>
            <div class="timeline-step ${stageClass(stages.rendering)}">
              <span class="step-dot"><i data-lucide="${stageIcon(stages.rendering)}" class="${stageSpin(stages.rendering)}" style="width:10px;height:10px;"></i></span>
              <span>Final Rendering</span>
            </div>
          </div>
        </div>
      `;
    }
    
    const statusClass = job.status === 'completed' ? 'status-completed' : 'status-rendering';
    const statusIcon = job.status === 'completed' ? 'check-circle' : 'alert-circle';
    
    return `
      <div class="job-item">
        <div>
          <div class="job-title">${escapeHtml(job.title)}</div>
          <div style="font-size: 0.8rem; color: var(--color-text-muted)">
            Style: ${escapeHtml(job.style_preset)}
          </div>
        </div>
        <span class="job-status ${statusClass}">
          <i data-lucide="${statusIcon}" style="width:12px;height:12px;display:inline-block;vertical-align:middle;margin-right:4px;"></i>
          ${job.status.toUpperCase()}
        </span>
      </div>
    `;
  }).join('');
  
  lucide.createIcons();
}

function renderHomeDashboard() {
  const drafts = state.diaries.filter(d => d.is_draft || d.id === '1' || d.id === '2');
  const activeStoryboards = document.getElementById('active-storyboards');
  
  if (activeStoryboards && drafts.length > 0) {
    activeStoryboards.innerHTML = drafts.slice(0, 3).map((draft, idx) => {
      const completion = idx === 0 ? 75 : 40;
      const statusText = idx === 0 ? 'Storyboard ready' : 'Stitching scene...';
      return `
        <div class="storyboard-item">
          <div class="storyboard-info">
            <h4>${escapeHtml(draft.title)}</h4>
            <p>${statusText} &bull; ${completion}% complete</p>
          </div>
          <div class="storyboard-progress">
            <div class="progress-bar-container">
              <div class="progress-bar" style="width: ${completion}%; background: ${idx === 0 ? 'var(--color-accent-rose)' : 'var(--color-accent-teal)'}"></div>
            </div>
          </div>
        </div>
      `;
    }).join('');
  }
  
  const completed = state.movies.filter(m => m.status === 'completed');
  const moviesGrid = document.getElementById('recent-movies-list');
  
  if (moviesGrid && completed.length > 0) {
    moviesGrid.innerHTML = completed.map(movie => `
      <div class="movie-card-mock" onclick="playMovie('${movie.id}')">
        <div class="movie-play-overlay">
          <i data-lucide="play-circle"></i>
        </div>
        <div class="movie-title">${escapeHtml(movie.title)}</div>
      </div>
    `).join('');
    lucide.createIcons();
  } else if (moviesGrid) {
    moviesGrid.innerHTML = '<div class="loading-state w-100">No compiled movies yet. Head to "Movies" tab to generate one!</div>';
  }
}

// WebSocket Connection for notifications
function connectWebSocket() {
  const wsUrl = `${WS_BASE_URL}/jobs/${DEFAULT_USER_ID}`;
  console.log(`Connecting WebSocket to ${wsUrl}`);
  
  try {
    state.ws = new WebSocket(wsUrl);
    
    state.ws.onopen = () => {
      console.log('WebSocket connection established.');
    };
    
    state.ws.onmessage = (event) => {
      console.log('WS Message received:', event.data);
      try {
        const data = JSON.parse(event.data);
        if (data.type === 'render_progress') {
          showToast(`Job "${data.title}": ${data.message}`, 'success');
          state.progress[data.title] = data.message;
          loadMovies();
        }
      } catch (e) {
        if (event.data.includes('Ping')) {
          console.log('WS Ping response received.');
        } else {
          showToast(event.data, 'info');
        }
      }
    };
    
    state.ws.onerror = (err) => {
      console.warn('WebSocket encountered error. Reconnecting...', err);
    };
    
    state.ws.onclose = () => {
      console.log('WebSocket closed. Retrying in 10s...');
      if (state.isLoggedIn) {
        setTimeout(connectWebSocket, 10000);
      }
    };
  } catch (err) {
    console.error('Failed to establish WebSocket connection:', err);
  }
}

// Helper to Escape HTML
function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#039;');
}

// Toast Notifications
function showToast(message, type = 'info') {
  const container = document.getElementById('toast-container');
  if (!container) return;
  
  const toast = document.createElement('div');
  toast.className = `toast toast-${type}`;
  
  let iconName = 'info';
  if (type === 'success') iconName = 'check-circle';
  if (type === 'error') iconName = 'alert-triangle';
  
  toast.innerHTML = `
    <i data-lucide="${iconName}"></i>
    <span>${message}</span>
  `;
  
  container.appendChild(toast);
  lucide.createIcons();
  
  setTimeout(() => {
    toast.style.animation = 'slideIn 0.3s reverse forwards';
    setTimeout(() => toast.remove(), 300);
  }, 4000);
}

// Play movie modal controller
window.playMovie = function(movieIdOrUrl) {
  let title = "Goa Trip 2024";
  let summary = "A beautiful family journey through the beaches of Goa. Captured with cinematic realism, narration, and background ambient sounds.";
  let url = movieIdOrUrl;
  
  if (movieIdOrUrl === 'mock-goa' || movieIdOrUrl.includes('d5602113')) {
    title = "Goa Trip 2024";
    url = "movies/d5602113-2025-4826-ac22-ff7ea73faac4.mp4";
  } else if (movieIdOrUrl === 'mock-birthday' || movieIdOrUrl.includes('e5ec0998')) {
    title = "Anaya's Birthday";
    url = "movies/e5ec0998-36d6-4128-a229-a4dd106d3c2f.mp4";
  } else {
    const movie = state.movies.find(m => m.id === movieIdOrUrl || m.rendered_video_url === movieIdOrUrl);
    if (movie) {
      title = movie.title;
      summary = movie.summary || "A beautiful memory movie compiled from your life timeline.";
      url = movie.rendered_video_url;
      // Resolve relative backend URLs to absolute ones
      if (url && url.startsWith('/') && !url.startsWith('//')) {
        const base = API_BASE_URL.replace('/api/v1', '');
        url = `${base}${url}`;
      }
    }
  }


  
  const modal = document.getElementById('video-modal');
  const player = document.getElementById('player');
  const titleEl = document.getElementById('modal-video-title');
  const summaryEl = document.getElementById('modal-video-summary');
  
  if (modal && player) {
    player.src = url;
    if (titleEl) titleEl.textContent = title;
    if (summaryEl) summaryEl.textContent = summary;
    
    modal.style.display = 'flex';
    player.play().catch(err => console.log("Auto-play blocked:", err));
  }
};

function initModal() {
  const modal = document.getElementById('video-modal');
  const player = document.getElementById('player');
  const closeBtn = document.getElementById('btn-close-modal');
  
  if (closeBtn && modal && player) {
    closeBtn.addEventListener('click', () => {
      player.pause();
      player.src = '';
      modal.style.display = 'none';
    });
    
    modal.addEventListener('click', (e) => {
      if (e.target === modal) {
        closeBtn.click();
      }
    });
  }
}
