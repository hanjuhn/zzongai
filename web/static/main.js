const statusEl = document.getElementById("status");
const backendUrlEl = document.getElementById("backend-url");
const backendBase = window.BACKEND_BASE || "http://localhost:8000";

backendUrlEl.textContent = backendBase;

const generateBtn = document.getElementById("generate-btn");
const generateBtnText = document.getElementById("generate-btn-text");
const generateBtnSpinner = document.getElementById("generate-btn-spinner");
const cancelBtn = document.getElementById("cancel-btn");
const generateMelodyBtn = document.getElementById("generate-melody-btn");
const melodyBtnText = document.getElementById("melody-btn-text");
const melodyBtnSpinner = document.getElementById("melody-btn-spinner");

const fileInput = document.getElementById("file-input");
const fileListEl = document.getElementById("file-list");
const textInput = document.getElementById("text-input");
const charCountEl = document.getElementById("char-count");
const studyTextEl = document.getElementById("study-text");
const lyricsTextEl = document.getElementById("lyrics-text");
const planTextEl = document.getElementById("plan-text");
const audioContainer = document.getElementById("audio-output");

const bubbleBox = document.querySelector(".bubble-box");
const characterImg = document.getElementById("character-img");

const emotionSection = document.getElementById("emotion-tags-section");
const emotionToggle = document.getElementById("emotion-tags-toggle");

const progressFill = document.getElementById("progress-fill");
const progressPercentEl = document.getElementById("progress-percent");

const saveBtn = document.getElementById("save-btn");

// 오디오 URL 목록 (다운로드용)
let currentAudioUrls = [];

// 진행바 상태
let currentProgress = 0;
let progressTimer = null;

// 선택된 파일들 관리
let selectedFiles = [];

// 가사 생성 취소를 위한 AbortController
let lyricsAbortController = null;

// 생성된 가사와 학습 텍스트 저장
let generatedLyrics = null;
let currentStudyText = null;

// 검색된 동요 정보 저장 (멜로디 생성 시 활용)
let retrievedDocs = null;
let reasonerResult = null;

// 선택된 감정 태그
let selectedEmotionTags = [];

// 감정 태그 목록
const emotionTags = [
  "통통튀는",
  "신나는",
  "슬픈",
  "밝은",
  "따뜻한",
  "차분한",
  "활기찬",
  "부드러운",
  "강렬한",
  "평화로운",
  "에너지 넘치는",
  "로맨틱한",
  "웃긴",
  "장난스러운",
  "진지한",
  "드라마틱한",
  "몽환적인",
  "우아한",
  "자유로운",
  "편안한",
];

// 진행바 제어
function setProgress(target) {
  target = Math.max(target, currentProgress);
  if (progressTimer) clearInterval(progressTimer);

  progressTimer = setInterval(() => {
    if (currentProgress >= target) {
      clearInterval(progressTimer);
      return;
    }
    currentProgress += 1;
    progressFill.style.width = currentProgress + "%";
    progressPercentEl.textContent = currentProgress + "%";
  }, 20);
}

function resetProgress() {
  if (progressTimer) clearInterval(progressTimer);
  currentProgress = 0;
  progressFill.style.width = "0%";
  progressPercentEl.textContent = "0%";
}

// 공통 유틸
function setStatus(message) {
  statusEl.textContent = message;
}

function setPre(el, value) {
  el.textContent = value?.trim() || "-";
}

function clearAudio() {
  audioContainer.innerHTML = "";
  audioContainer.append("");

  if (saveBtn) {
    saveBtn.disabled = true;
    saveBtn.classList.remove("active");
  }

  const placeholder = document.createElement("button");
  placeholder.className = "audio-btn";
  placeholder.disabled = true;
  placeholder.textContent = "아직 생성된 오디오가 없습니다";

  audioContainer.appendChild(placeholder);
  currentAudioUrls = [];
}

function downloadAudio(url, filename) {
  fetch(url)
    .then((response) => response.blob())
    .then((blob) => {
      const downloadUrl = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = downloadUrl;
      a.download = filename || "learning-song.mp3";
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      window.URL.revokeObjectURL(downloadUrl);
    })
    .catch((error) => {
      console.error("डाउन로드 실패:", error);
      alert("오디오 다운로드에 실패했습니다.");
    });
}

// 오른쪽 카드의 커스텀 뮤직 플레이어 렌더링
function renderAudio(urls) {
  audioContainer.innerHTML = "";
  currentAudioUrls = urls || [];

  if (!urls || urls.length === 0) {
    clearAudio();
    return;
  }

  urls.forEach((url, index) => {
    const item = document.createElement("div");
    item.className = "audio-item";

    const header = document.createElement("div");
    header.className = "audio-header";

    const label = document.createElement("span");
    label.className = "audio-label";
    label.textContent = `노래 ${index + 1}`;

    header.appendChild(label);

    const audio = document.createElement("audio");
    audio.src = url;

    const wrapper = document.createElement("div");
    wrapper.className = "audio-player";

    const playBtn = document.createElement("button");
    playBtn.className = "audio-play-btn";
    playBtn.textContent = "▶";

    const progress = document.createElement("input");
    progress.type = "range";
    progress.min = 0;
    progress.max = 100;
    progress.value = 0;
    progress.className = "audio-progress";

    const timeLabel = document.createElement("span");
    timeLabel.className = "audio-time";
    timeLabel.textContent = "00:00 / 00:00";

    function formatTime(sec) {
      const m = Math.floor(sec / 60)
        .toString()
        .padStart(2, "0");
      const s = Math.floor(sec % 60)
        .toString()
        .padStart(2, "0");
      return `${m}:${s}`;
    }

    audio.addEventListener("loadedmetadata", () => {
      timeLabel.textContent = `00:00 / ${formatTime(audio.duration)}`;
    });

    playBtn.addEventListener("click", () => {
      if (audio.paused) {
        audio.play();
        playBtn.textContent = "⏸";
      } else {
        audio.pause();
        playBtn.textContent = "▶";
      }
    });

    audio.addEventListener("timeupdate", () => {
      if (!isNaN(audio.duration) && audio.duration > 0) {
        const percent = (audio.currentTime / audio.duration) * 100;
        progress.value = percent;
        timeLabel.textContent = `${formatTime(
          audio.currentTime
        )} / ${formatTime(audio.duration)}`;
      }
    });

    progress.addEventListener("input", () => {
      if (!isNaN(audio.duration) && audio.duration > 0) {
        const nextTime = (progress.value / 100) * audio.duration;
        audio.currentTime = nextTime;
      }
    });

    audio.addEventListener("ended", () => {
      playBtn.textContent = "▶";
      progress.value = 0;
      timeLabel.textContent = `00:00 / ${formatTime(audio.duration)}`;
    });

    wrapper.appendChild(playBtn);
    wrapper.appendChild(progress);
    wrapper.appendChild(timeLabel);

    audio.style.display = "none";
    wrapper.appendChild(audio);

    item.appendChild(header);
    item.appendChild(wrapper);

    audioContainer.appendChild(item);
  });

  if (saveBtn) {
    saveBtn.disabled = false;
    saveBtn.classList.add("active");
  }
}

// 곡 선택 모달 관련
const downloadModal = document.getElementById("download-modal");
const downloadOptions = document.getElementById("download-options");
const downloadCancelBtn = downloadModal.querySelector(".download-modal-cancel");

function openDownloadModal() {
  if (!currentAudioUrls || currentAudioUrls.length === 0) {
    alert("다운로드할 오디오가 없습니다.");
    return;
  }

  if (currentAudioUrls.length === 1) {
    downloadAudio(currentAudioUrls[0], "zzongal-song-1.mp3");
    return;
  }

  downloadOptions.innerHTML = "";

  currentAudioUrls.forEach((url, index) => {
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "download-option-btn";
    btn.textContent = `노래 ${index + 1} 저장`;

    btn.addEventListener("click", () => {
      downloadAudio(url, `zzongal-song-${index + 1}.mp3`);
      closeDownloadModal();
    });

    downloadOptions.appendChild(btn);
  });

  downloadModal.classList.remove("hidden");
}

function closeDownloadModal() {
  downloadModal.classList.add("hidden");
  downloadOptions.innerHTML = "";
}

downloadCancelBtn.addEventListener("click", closeDownloadModal);

downloadModal.addEventListener("click", (e) => {
  if (e.target === downloadModal) {
    closeDownloadModal();
  }
});

// 파일 목록 & 입력 관리
function updateFileList() {
  fileListEl.innerHTML = "";
  if (selectedFiles.length === 0) {
    return;
  }

  selectedFiles.forEach((file, index) => {
    const item = document.createElement("div");
    item.className = "file-item";

    const fileName = document.createElement("span");
    fileName.className = "file-name";
    fileName.textContent = file.name;

    const fileType = document.createElement("span");
    fileType.className = "file-type";
    fileType.textContent = file.type === "application/pdf" ? "PDF" : "이미지";

    const removeBtn = document.createElement("button");
    removeBtn.textContent = "삭제";
    removeBtn.onclick = () => {
      selectedFiles.splice(index, 1);
      updateFileList();
      updateFileInput();
    };

    item.appendChild(fileName);
    item.appendChild(fileType);
    item.appendChild(removeBtn);
    fileListEl.appendChild(item);
  });
}

function updateFileInput() {
  const dt = new DataTransfer();
  selectedFiles.forEach((file) => dt.items.add(file));
  fileInput.files = dt.files;
}

fileInput.addEventListener("change", (e) => {
  const files = Array.from(e.target.files);
  const images = files.filter((f) => f.type.startsWith("image/"));
  const pdfs = files.filter((f) => f.type === "application/pdf");

  const currentImages = selectedFiles.filter((f) =>
    f.type.startsWith("image/")
  );
  if (currentImages.length + images.length > 5) {
    alert("이미지는 최대 5장까지 업로드할 수 있습니다.");
    return;
  }

  const currentPdfs = selectedFiles.filter((f) => f.type === "application/pdf");
  if (currentPdfs.length + pdfs.length > 1) {
    alert("PDF는 최대 1개까지 업로드할 수 있습니다.");
    return;
  }

  selectedFiles.push(...files);
  updateFileList();
  updateFileInput();
});

// 글자수 카운트
function updateCharCount() {
  const length = textInput.value.length;
  const maxLength = 300;
  charCountEl.textContent = `${length} / ${maxLength}`;

  charCountEl.classList.remove("warning", "error");
  if (length > maxLength * 0.9) {
    charCountEl.classList.add("error");
  } else if (length > maxLength * 0.7) {
    charCountEl.classList.add("warning");
  }
}

textInput.addEventListener("input", updateCharCount);
textInput.addEventListener("paste", () => {
  setTimeout(updateCharCount, 0);
});

// 버튼 로딩 상태
function setButtonLoading(button, textEl, spinnerEl, isLoading, loadingText) {
  if (isLoading) {
    button.disabled = true;
    if (loadingText) {
      textEl.textContent = loadingText;
    }
    spinnerEl.style.display = "inline-block";
    spinnerEl.style.animation = "spin 1s linear infinite";
  } else {
    button.disabled = false;
    spinnerEl.style.display = "none";
    spinnerEl.style.animation = "none";
  }
}

function disableControls() {
  generateBtn.disabled = true;
  fileInput.disabled = true;
  textInput.disabled = true;
}

function enableControls() {
  generateBtn.disabled = false;
  fileInput.disabled = false;
  textInput.disabled = false;
}

function showCancelButton() {
  cancelBtn.style.display = "inline-block";
}

function hideCancelButton() {
  cancelBtn.style.display = "none";
}

function showMelodyButton() {
  generateMelodyBtn.style.display = "inline-block";
}

function hideMelodyButton() {
  generateMelodyBtn.style.display = "none";
}

// HTTP helpers
async function postJSON(path, payload, signal = null) {
  const options = {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  };
  if (signal) {
    options.signal = signal;
  }

  const resp = await fetch(`${backendBase}${path}`, options);

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${path} 요청 실패 (${resp.status}): ${text}`);
  }

  return resp.json();
}

async function postFormData(path, formData) {
  const resp = await fetch(`${backendBase}${path}`, {
    method: "POST",
    body: formData,
  });

  if (!resp.ok) {
    const text = await resp.text();
    throw new Error(`${path} 요청 실패 (${resp.status}): ${text}`);
  }

  return resp.json();
}

/* ----------------- 가사 생성 단계 ----------------- */
async function handleGenerate() {
  try {
    disableControls();
    hideMelodyButton();
    resetProgress();
    setProgress(5);

    const inputText = textInput.value.trim();
    const hasFiles = selectedFiles.length > 0;

    if (!inputText && !hasFiles) {
      throw new Error("텍스트를 입력하거나 파일을 업로드해주세요.");
    }

    if (inputText.length > 300) {
      throw new Error("텍스트는 300자를 초과할 수 없습니다.");
    }

    clearAudio();
    setPre(studyTextEl, "-");
    setPre(lyricsTextEl, "-");
    setPre(planTextEl, "-");
    generatedLyrics = null;
    currentStudyText = null;
    retrievedDocs = null;
    reasonerResult = null;

    let studyText = "";

    if (inputText) {
      studyText = inputText;
      setStatus("입력된 텍스트 사용 중...");
      setPre(studyTextEl, studyText);
    } else if (hasFiles) {
      setStatus("파일 분석 중...");
      setButtonLoading(
        generateBtn,
        generateBtnText,
        generateBtnSpinner,
        true,
        "파일 분석 중..."
      );
      bubbleBox.innerHTML = "파일에서 내용을 추출하고 있어요...";

      const formData = new FormData();
      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });

      const extractResp = await postFormData("/extract-from-files", formData);
      studyText = extractResp.study_text?.trim();

      if (!studyText) {
        throw new Error("파일에서 내용을 추출하지 못했습니다.");
      }

      setPre(studyTextEl, studyText);
      setButtonLoading(generateBtn, generateBtnText, generateBtnSpinner, false);
      generateBtnText.textContent = "가사 생성";
    }

    if (!studyText) {
      throw new Error("처리할 텍스트가 없습니다.");
    }

    currentStudyText = studyText;

    // 가사 생성 시작
    setStatus("가사 생성 중...");
    setButtonLoading(
      generateBtn,
      generateBtnText,
      generateBtnSpinner,
      true,
      "가사 생성 중..."
    );
    bubbleBox.innerHTML =
      "쫑알 가사를 만드는 중이에요...<br>잠시만 기다려 주세요!";
    showCancelButton();
    setProgress(20);

    lyricsAbortController = new AbortController();

    try {
      const lyricsResp = await postJSON(
        "/generate-lyrics",
        { study_text: studyText },
        lyricsAbortController.signal
      );

      generatedLyrics = lyricsResp.lyrics || "";
      retrievedDocs = lyricsResp.retrieved_docs || null;
      reasonerResult = lyricsResp.reasoner_result || null;

      setPre(lyricsTextEl, generatedLyrics || "(가사가 비어 있습니다)");
      setStatus("가사 생성 완료! 멜로디 생성을 진행해 주세요.");
      bubbleBox.innerHTML =
        "가사가 완성되었어요!<br>이제 멜로디를 만들어 볼까요?";
      setProgress(40);
      showMelodyButton();
    } catch (error) {
      if (error.name === "AbortError") {
        setStatus("가사 생성이 중단되었습니다.");
        setPre(lyricsTextEl, "-");
        bubbleBox.innerHTML = "가사 생성을 중단했어요.";
      } else {
        throw error;
      }
    } finally {
      hideCancelButton();
      lyricsAbortController = null;
      setButtonLoading(generateBtn, generateBtnText, generateBtnSpinner, false);
      generateBtnText.textContent = "가사 생성";
      enableControls();
    }
  } catch (error) {
    console.error(error);
    setStatus(`에러: ${error.message || error}`);
    hideCancelButton();
    lyricsAbortController = null;
    setButtonLoading(generateBtn, generateBtnText, generateBtnSpinner, false);
    generateBtnText.textContent = "가사 생성";
    bubbleBox.innerHTML = "에러가 발생했어요. 다시 시도해 주세요.";
    resetProgress();
  } finally {
    enableControls();
  }
}

async function handleCancel() {
  if (lyricsAbortController) {
    lyricsAbortController.abort();
    hideCancelButton();
    setStatus("가사 생성 중단 중...");
  }
}

/* ----------------- 멜로디 생성 단계 ----------------- */
async function handleGenerateMelody() {
  if (!generatedLyrics || !currentStudyText) {
    setStatus("먼저 가사를 생성해주세요.");
    return;
  }

  try {
    disableControls();
    setButtonLoading(
      generateMelodyBtn,
      melodyBtnText,
      melodyBtnSpinner,
      true,
      "멜로디 생성 중..."
    );
    resetProgress();
    setProgress(10);

    // 캐릭터/말풍선 초기화
    if (characterImg) {
      characterImg.src = "/static/asset/character1.svg";
      characterImg.classList.remove("character2");
      characterImg.classList.add("character1");
    }
    bubbleBox.innerHTML =
      "지금 쫑알을 준비하고 있어요.<br>잠시만 기다려 주세요!";

    setStatus("멜로디 가이드 생성 중...");
    const planResp = await postJSON("/mnemonic-plan", {
      study_text: currentStudyText,
      lyrics: generatedLyrics,
    });
    const mnemonicPlan = planResp.mnemonic_plan || "";
    setPre(
      planTextEl,
      mnemonicPlan || "(멜로디 가이드를 생성하지 못했습니다.)"
    );
    setProgress(40);

    setStatus("Suno 노래 생성 중...");
    setProgress(80);

    const songResp = await postJSON("/generate-song", {
      study_text: currentStudyText,
      mnemonic_plan: mnemonicPlan,
      lyrics: generatedLyrics,
      wait_for_audio: true, // 멜로디 생성은 항상 완료까지 대기
      emotion_tags: selectedEmotionTags,
      retrieved_docs: retrievedDocs,
      reasoner_result: reasonerResult,
    });

    renderAudio(songResp.audio_urls || []);

    if (songResp.audio_urls && songResp.audio_urls.length > 0) {
      setStatus("완료! 곡을 재생해보세요.");
      setProgress(100);
      bubbleBox.innerHTML =
        "쫑알이 완성되었어요!<br>아래에서 노래를 들어보세요 🎵";
      if (characterImg) {
        characterImg.src = "/static/asset/character2.svg";
        characterImg.classList.remove("character1");
        characterImg.classList.add("character2");
      }
    } else {
      setStatus("생성 완료. 오디오 URL을 응답에서 찾지 못했습니다.");
      bubbleBox.innerHTML =
        "노래 생성은 되었지만,<br>오디오를 불러오지 못했어요.";
    }
  } catch (error) {
    console.error(error);
    setStatus(`에러: ${error.message || error}`);
    bubbleBox.innerHTML = "멜로디 생성 중 에러가 발생했어요.";
    resetProgress();
  } finally {
    setButtonLoading(generateMelodyBtn, melodyBtnText, melodyBtnSpinner, false);
    melodyBtnText.textContent = "멜로디 생성";
    enableControls();
  }
}

/* ----------------- 감정 태그 UI ----------------- */
function initEmotionTags() {
  const container = document.getElementById("emotion-tags-container");
  if (!container) return;

  container.innerHTML = "";

  emotionTags.forEach((tag) => {
    const tagBtn = document.createElement("button");
    tagBtn.type = "button";
    tagBtn.className = "emotion-tag";
    tagBtn.textContent = tag;
    tagBtn.dataset.tag = tag;

    tagBtn.addEventListener("click", () => {
      toggleEmotionTag(tag);
    });

    container.appendChild(tagBtn);
  });

  updateEmotionTagsCount();
}

function toggleEmotionTag(tag) {
  const index = selectedEmotionTags.indexOf(tag);

  if (index > -1) {
    selectedEmotionTags.splice(index, 1);
  } else {
    if (selectedEmotionTags.length >= 5) {
      alert("감정 태그는 최대 5개까지 선택할 수 있습니다.");
      return;
    }
    selectedEmotionTags.push(tag);
  }

  updateEmotionTagsUI();
  updateEmotionTagsCount();
}

function updateEmotionTagsUI() {
  const tags = document.querySelectorAll(".emotion-tag");
  tags.forEach((tagBtn) => {
    const tag = tagBtn.dataset.tag;
    if (selectedEmotionTags.includes(tag)) {
      tagBtn.classList.add("selected");
    } else {
      tagBtn.classList.remove("selected");
    }

    if (selectedEmotionTags.length >= 5 && !selectedEmotionTags.includes(tag)) {
      tagBtn.classList.add("disabled");
    } else {
      tagBtn.classList.remove("disabled");
    }
  });
}

function updateEmotionTagsCount() {
  const countDisplay = document.getElementById("emotion-tags-count");
  if (!countDisplay) return;

  countDisplay.textContent = `${selectedEmotionTags.length} / 5개 선택됨`;
  if (selectedEmotionTags.length >= 5) {
    countDisplay.style.color = "#ef4444";
  } else {
    countDisplay.style.color = "#667295";
  }
}

/* ----------------- 초기화 & 이벤트 바인딩 ----------------- */

initEmotionTags();
clearAudio();
updateCharCount();
resetProgress();

generateBtn.addEventListener("click", handleGenerate);
cancelBtn.addEventListener("click", handleCancel);
generateMelodyBtn.addEventListener("click", handleGenerateMelody);

if (saveBtn) {
  saveBtn.addEventListener("click", () => {
    if (!currentAudioUrls || currentAudioUrls.length === 0) {
      alert("다운로드할 오디오가 없습니다.");
      return;
    }
    openDownloadModal();
  });
}
if (emotionToggle && emotionSection) {
  emotionToggle.addEventListener("click", () => {
    emotionSection.classList.toggle("open");
  });
}
