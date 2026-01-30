/**
 * Guess Keith Ward - Cosmic Edition
 * A supernatural journey through theological mystery
 */

let currentQuestionId = null;

const screenList = document.getElementById("screen-list");
const screenGuess = document.getElementById("screen-guess");

const listEl = document.getElementById("question-list");
const btnRefresh = document.getElementById("btn-refresh");

const btnBack = document.getElementById("btn-back");
const qTitle = document.getElementById("q-title");
const qText = document.getElementById("q-text");
const guessForm = document.getElementById("guess-form");
const btnSubmit = document.getElementById("btn-submit");
const btnRead = document.getElementById("btn-read");

const feedback = document.getElementById("feedback");
const answerBox = document.getElementById("answer-box");
const answerText = document.getElementById("answer-text");

const emojiCelebration = document.getElementById("emoji-celebration");

// Celebration emojis for correct answers
const correctEmojis = ['🎉', '🥂', '✨', '🌟', '💫', '🎊', '⭐', '🏆', '👏', '🙌'];
const incorrectEmojis = ['😔', '💭', '🤔', '📚', '🌙', '💫'];

// Messages
const correctMessages = [
  "Brilliant! You've penetrated the theological veil.",
  "Exactly right! Your insight is finely tuned.",
  "You've discerned the truth. The mystery reveals itself.",
  "Transcendent insight! You walk the path of understanding.",
  "The stars align with your perception."
];

const incorrectMessages = [
  "Not quite... The answer lies along a more nuanced path.",
  "Close, but the theological current flows elsewhere.",
  "The mystery deepens. Consider the middle way.",
  "Almost... Ward's position tends toward greater subtlety.",
  "A thoughtful guess, but not the one Ward would make."
];

function showList() {
  screenGuess.classList.add("hidden");
  screenList.classList.remove("hidden");
  currentQuestionId = null;
}

function showGuess() {
  screenList.classList.add("hidden");
  screenGuess.classList.remove("hidden");
}

async function fetchJSON(url, opts) {
  const res = await fetch(url, opts);
  if (!res.ok) {
    const t = await res.text();
    throw new Error(t || `Request failed: ${res.status}`);
  }
  return res.json();
}

// Emoji celebration animation
function triggerCelebration(isCorrect) {
  emojiCelebration.innerHTML = '';

  const emojis = isCorrect ? correctEmojis : incorrectEmojis;
  const count = isCorrect ? 30 : 8;

  for (let i = 0; i < count; i++) {
    const emoji = document.createElement('div');
    emoji.className = 'floating-emoji';
    emoji.textContent = emojis[Math.floor(Math.random() * emojis.length)];

    // Random position and animation
    emoji.style.left = Math.random() * 100 + '%';
    emoji.style.animationDelay = Math.random() * 0.5 + 's';
    emoji.style.fontSize = (isCorrect ? 24 + Math.random() * 24 : 20 + Math.random() * 12) + 'px';

    emojiCelebration.appendChild(emoji);
  }

  // Clean up after animation
  setTimeout(() => {
    emojiCelebration.innerHTML = '';
  }, 3000);
}

async function loadQuestions() {
  listEl.innerHTML = '<div class="loading">Channeling the mysteries...</div>';

  try {
    const items = await fetchJSON("/api/questions");
    listEl.innerHTML = "";

    for (const q of items) {
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `<h3>${escapeHTML(q.title)}</h3><p>${escapeHTML(q.question_preview)}</p>`;
      div.addEventListener("click", () => openQuestion(q.id));
      listEl.appendChild(div);
    }
  } catch (err) {
    listEl.innerHTML = `<div class="loading">Error summoning questions: ${escapeHTML(err.message)}</div>`;
  }
}

function escapeHTML(s) {
  return (s ?? "").replace(/[&<>"']/g, c => ({
    "&": "&amp;", "<": "&lt;", ">": "&gt;", "\"": "&quot;", "'": "&#39;"
  }[c]));
}

async function openQuestion(id) {
  currentQuestionId = id;
  feedback.classList.add("hidden");
  feedback.classList.remove("correct", "incorrect");
  feedback.textContent = "";
  btnRead.classList.add("hidden");
  answerBox.classList.add("hidden");
  answerText.textContent = "";

  const q = await fetchJSON(`/api/questions/${id}`);
  qTitle.textContent = q.title;
  qText.textContent = q.question_text || "(The question awaits revelation...)";

  guessForm.innerHTML = "";
  const letters = ["A", "B", "C", "D", "E"];
  q.choices.forEach((choiceText, idx) => {
    const letter = letters[idx];
    const wrapper = document.createElement("div");
    wrapper.className = "choice";
    wrapper.innerHTML = `
      <label>
        <input type="radio" name="choice" value="${letter}" ${idx === 0 ? "checked" : ""}/>
        <div><strong>${letter}.</strong> ${escapeHTML(choiceText)}</div>
      </label>`;
    guessForm.appendChild(wrapper);
  });

  showGuess();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function getSelectedChoice() {
  const input = guessForm.querySelector('input[name="choice"]:checked');
  return input ? input.value : "A";
}

function getRandomMessage(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

btnSubmit.addEventListener("click", async (e) => {
  e.preventDefault();
  if (!currentQuestionId) return;

  btnSubmit.textContent = "Consulting the cosmos...";
  btnSubmit.disabled = true;

  try {
    const choice = getSelectedChoice();
    const resp = await fetchJSON("/api/submit", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question_id: currentQuestionId, choice })
    });

    feedback.classList.remove("hidden", "correct", "incorrect");

    if (resp.correct) {
      feedback.classList.add("correct");
      const message = getRandomMessage(correctMessages);
      feedback.innerHTML = `
        <div class="result-header">🎉 Correct!</div>
        <p>${message}</p>
        <p class="hint-text">${resp.explanation || ""}</p>
      `;
      triggerCelebration(true);
    } else {
      feedback.classList.add("incorrect");
      const message = getRandomMessage(incorrectMessages);
      feedback.innerHTML = `
        <div class="result-header">😔 Not quite...</div>
        <p>${message}</p>
        <p class="hint-text">${resp.hint || ""}</p>
        <p class="correct-answer">The answer was <strong>${resp.correct_choice}</strong></p>
      `;
      triggerCelebration(false);
    }

    btnRead.classList.remove("hidden");
    feedback.scrollIntoView({ behavior: 'smooth', block: 'center' });

  } catch (err) {
    feedback.classList.remove("hidden");
    feedback.textContent = `A cosmic disturbance: ${err.message}`;
  } finally {
    btnSubmit.textContent = "Seal My Divination";
    btnSubmit.disabled = false;
  }
});

btnRead.addEventListener("click", async () => {
  if (!currentQuestionId) return;

  btnRead.textContent = "Unveiling...";
  btnRead.disabled = true;

  try {
    const a = await fetchJSON(`/api/questions/${currentQuestionId}/answer`);
    answerBox.classList.remove("hidden");
    answerText.textContent = a.answer_text || "(Ward's answer transcends mere words...)";
    answerBox.scrollIntoView({ behavior: 'smooth', block: 'start' });
  } finally {
    btnRead.textContent = "Reveal Ward's Wisdom";
    btnRead.disabled = false;
  }
});

btnBack.addEventListener("click", () => {
  showList();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

// Return button at bottom of answer
document.getElementById("btn-return").addEventListener("click", () => {
  showList();
  window.scrollTo({ top: 0, behavior: 'smooth' });
});

btnRefresh.addEventListener("click", () => loadQuestions());

// Keyboard navigation
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !screenGuess.classList.contains('hidden')) {
    showList();
  }
});

// Initialize
console.log('✧ Guess Keith Ward - Cosmic Edition ✧');
loadQuestions().catch(err => {
  listEl.innerHTML = `<div class="loading">The cosmic connection falters: ${escapeHTML(err.message)}</div>`;
});
