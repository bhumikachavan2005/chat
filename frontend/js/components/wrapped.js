/**
 * Friendship Wrapped - Pure Private Photos Vault
 * - Focuses ONLY on personal photos of Vinu 💝 & Bhuu 🎀
 * - All text/stat stories removed
 * - Dedicated Secret PIN protection
 * - Large, beautiful, uncropped photo viewing with captions
 * - Direct "📸 Add Photo" & "🗑️ Delete Photo" management
 */

const WrappedComponent = {
  storyData: null,
  currentSlideIndex: 0,
  timer: null,
  slideDurationMs: 7000,
  isPaused: false,
  isUnlockedInSession: false,
  photoEventsBound: false,

  async open() {
    console.log("[Wrapped] open() called");
    if (window.App && typeof window.App.showToast === "function") {
      window.App.showToast("🎁 Opening Secret Photos Vault...");
    }

    // Check if secret PIN protection is active
    try {
      const pinStatus = await API.wrapped.getPinStatus();
      if (!this.isUnlockedInSession) {
        if (!pinStatus || !pinStatus.has_pin) {
          // No PIN set yet -> Prompt to set a secret PIN
          this.showPinModal(true);
          return;
        } else {
          // PIN is active -> Prompt to unlock with secret PIN
          this.showPinModal(false);
          return;
        }
      }
    } catch (err) {
      console.warn("[Wrapped] Failed to check PIN status, proceeding:", err);
    }

    await this.launchPresentation();
  },

  showPinModal(isSetupMode = false) {
    const pinModal = document.getElementById("wrappedPinModal");
    const pinInput = document.getElementById("inputWrappedPin");
    const pinError = document.getElementById("wrappedPinError");
    const btnClose = document.getElementById("btnCloseWrappedPinModal");
    const form = document.getElementById("formWrappedPin");
    const title = document.getElementById("wrappedPinTitle");
    const desc = document.getElementById("wrappedPinDesc");
    const submitText = document.getElementById("wrappedPinSubmitText");

    if (!pinModal) return;

    if (pinInput) pinInput.value = "";
    if (pinError) {
      pinError.textContent = "";
      pinError.classList.add("hidden");
    }

    if (isSetupMode) {
      if (title) title.textContent = "🔒 Set Secret Wrapped PIN";
      if (desc) desc.textContent = "Create a secret 4-digit PIN for Wrapped to keep Vinu 💝 × Bhuu 🎀 Private Photos protected.";
      if (submitText) submitText.textContent = "Set PIN & Open Photos";
    } else {
      if (title) title.textContent = "🔒 Secret Wrapped Vault";
      if (desc) desc.textContent = "Enter your secret PIN to unlock Vinu 💝 × Bhuu 🎀 Private Photos.";
      if (submitText) submitText.textContent = "Unlock & Open Photos";
    }

    pinModal.classList.remove("hidden");
    pinModal.style.display = "flex";
    setTimeout(() => { if (pinInput) pinInput.focus(); }, 100);

    if (btnClose) {
      btnClose.onclick = () => {
        pinModal.classList.add("hidden");
        pinModal.style.display = "none";
      };
    }

    if (form) {
      form.onsubmit = async (e) => {
        e.preventDefault();
        const pinVal = document.getElementById("inputWrappedPin")?.value || "";
        if (!pinVal) return;

        try {
          if (isSetupMode) {
            await API.wrapped.setPin(pinVal);
            this.isUnlockedInSession = true;
            pinModal.classList.add("hidden");
            pinModal.style.display = "none";
            if (window.App) window.App.showToast("🔒 Secret PIN set successfully!");
            await this.launchPresentation();
          } else {
            const res = await API.wrapped.verifyPin(pinVal);
            if (res && res.unlocked) {
              this.isUnlockedInSession = true;
              pinModal.classList.add("hidden");
              pinModal.style.display = "none";
              await this.launchPresentation();
            }
          }
        } catch (err) {
          if (pinError) {
            pinError.textContent = err.message || "Incorrect Secret PIN.";
            pinError.classList.remove("hidden");
          }
        }
      };
    }
  },

  async launchPresentation() {
    const modal = document.getElementById("wrappedModal");
    if (!modal) {
      console.error("[Wrapped] wrappedModal element not found in DOM");
      return;
    }

    modal.classList.remove("hidden");
    modal.style.display = "flex";
    document.body.style.overflow = "hidden";

    if (!this.storyData) {
      const card = document.getElementById("wrappedSlideCard");
      if (card) {
        card.innerHTML = `
          <div style="text-align: center; padding: 3rem 1rem;">
            <div class="spinner" style="width: 40px; height: 40px; margin: 0 auto 1.5rem auto; border-top-color: #ec4899;"></div>
            <h3 style="font-size: 1.25rem; font-weight: 700; color: #fff; margin-bottom: 0.5rem;">Loading Secret Photos...</h3>
            <p style="font-size: 0.85rem; color: rgba(255, 255, 255, 0.7);">Preparing Vinu 💝 × Bhuu 🎀 Private Photo Vault</p>
          </div>
        `;
      }

      try {
        this.storyData = await API.wrapped.getStory();
      } catch (err) {
        console.error("Failed to load photo vault data:", err);
        if (window.App) window.App.showToast("Failed to load photos: " + err.message);
        this.close();
        return;
      }
    }

    this.currentSlideIndex = 0;
    this.renderSlide(0);
    this.startSlideTimer();
    this.bindControls();
    this.bindPhotoUploadControls();
  },

  close() {
    this.stopSlideTimer();
    const modal = document.getElementById("wrappedModal");
    if (modal) {
      modal.classList.add("hidden");
      modal.style.display = "none";
    }
    document.body.style.overflow = "";
  },

  renderSlide(index) {
    if (!this.storyData || !this.storyData.slides) return;
    const slides = this.storyData.slides;
    if (index < 0) index = 0;
    if (index >= slides.length) {
      this.close();
      return;
    }

    this.currentSlideIndex = index;
    const slide = slides[index];

    // Render Progress Bars at Top
    const progressContainer = document.getElementById("wrappedProgressBars");
    if (progressContainer) {
      if (slide.is_empty || slides.length <= 1) {
        progressContainer.innerHTML = "";
      } else {
        progressContainer.innerHTML = slides.map((_, i) => `
          <div class="wrapped-progress-track">
            <div class="wrapped-progress-fill ${i < index ? 'completed' : (i === index ? 'active' : '')}"></div>
          </div>
        `).join("");
      }
    }

    // Render Slide Card
    const card = document.getElementById("wrappedSlideCard");
    if (card) {
      if (slide.is_empty) {
        // Vault is empty state
        card.style.background = "linear-gradient(135deg, #181824 0%, #24142c 50%, #31133f 100%)";
        card.innerHTML = `
          <div style="padding: 2.5rem 1.5rem; text-align: center; display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%;">
            <div style="font-size: 4rem; margin-bottom: 0.75rem; animation: floatIcon 3s ease-in-out infinite;">📸</div>
            <h2 style="font-size: 1.45rem; font-weight: 800; color: #ffffff; margin-bottom: 0.5rem; text-shadow: 0 2px 8px rgba(0,0,0,0.8);">
              Secret Photo Vault is Empty
            </h2>
            <p style="font-size: 0.88rem; color: rgba(255, 255, 255, 0.75); line-height: 1.55; max-width: 310px; margin: 0 auto 1.5rem auto;">
              No photos added yet! Keep your favorite private memories of Vinu 💝 & Bhuu 🎀 right here.
            </p>
            <button id="btnEmptyAddPhoto" class="btn btn-primary" style="padding: 0.65rem 1.5rem; font-size: 0.92rem; border-radius: 24px; box-shadow: 0 8px 25px rgba(236, 72, 153, 0.4);">
              <span>📸 Add First Photo</span>
            </button>
          </div>
        `;

        const btnEmptyAdd = document.getElementById("btnEmptyAddPhoto");
        if (btnEmptyAdd) {
          btnEmptyAdd.onclick = () => {
            const btnAdd = document.getElementById("btnWrappedAddPhoto");
            if (btnAdd) btnAdd.click();
          };
        }
      } else {
        // Real Photo Showcase
        card.style.background = "linear-gradient(135deg, #0d0f18 0%, #171124 50%, #1e112b 100%)";
        card.innerHTML = `
          <div class="wrapped-photo-view-box" style="display: flex; flex-direction: column; align-items: center; justify-content: center; height: 100%; padding: 0.5rem 0.25rem;">
            
            <!-- Main Photo Display -->
            <div class="wrapped-photo-wrapper" style="position: relative; width: 100%; display: flex; justify-content: center; align-items: center; max-height: 480px; min-height: 280px; border-radius: 18px; overflow: hidden; background: rgba(0, 0, 0, 0.5); border: 1px solid rgba(255, 255, 255, 0.16); box-shadow: 0 16px 45px rgba(0, 0, 0, 0.85);">
              <img src="${slide.photo_url}" alt="${this.escapeHtml(slide.caption || 'Memory')}" style="max-height: 470px; width: auto; max-width: 100%; object-fit: contain; border-radius: 14px; display: block; margin: 0 auto;">
            </div>

            <!-- Caption & Controls -->
            <div style="margin-top: 1rem; width: 100%; text-align: center; padding: 0 0.75rem;">
              ${slide.caption ? `
                <div style="font-size: 1.05rem; font-weight: 600; color: #ffffff; text-shadow: 0 2px 8px rgba(0,0,0,0.9); line-height: 1.35; margin-bottom: 0.35rem;">
                  "${this.escapeHtml(slide.caption)}"
                </div>
              ` : `
                <div style="font-size: 0.85rem; color: rgba(255,255,255,0.6); font-style: italic; margin-bottom: 0.35rem;">
                  Special Memory
                </div>
              `}

              <div style="display: flex; align-items: center; justify-content: center; gap: 0.85rem; margin-top: 0.5rem;">
                <span style="font-size: 0.75rem; color: rgba(255,255,255,0.75); font-weight: 700; background: rgba(0,0,0,0.45); padding: 0.25rem 0.65rem; border-radius: 14px; border: 1px solid rgba(255,255,255,0.1);">
                  Photo ${index + 1} of ${slides.length}
                </span>
                <button class="btn-slide-delete-photo" data-photo-id="${slide.photo_id}" title="Remove photo from vault">
                  🗑️ Delete
                </button>
              </div>
            </div>

          </div>
        `;

        // Direct delete handler
        card.querySelectorAll(".btn-slide-delete-photo").forEach(btn => {
          btn.onclick = async (e) => {
            e.stopPropagation();
            const photoId = parseInt(btn.dataset.photoId);
            if (!confirm("Are you sure you want to delete this photo from your Secret Vault?")) return;
            try {
              await API.wrapped.deletePhoto(photoId);
              if (window.App) window.App.showToast("Photo deleted.");
              this.storyData = null;
              this.storyData = await API.wrapped.getStory();
              this.renderSlide(Math.max(0, Math.min(this.currentSlideIndex, this.storyData.slides.length - 1)));
            } catch (err) {
              alert("Error deleting photo: " + err.message);
            }
          };
        });
      }
    }

    if (!slide.is_empty && (index === 0 || index === slides.length - 1)) {
      this.triggerConfetti();
    }
  },

  nextSlide() {
    if (!this.storyData || !this.storyData.slides) return;
    if (this.currentSlideIndex < this.storyData.slides.length - 1) {
      this.renderSlide(this.currentSlideIndex + 1);
      this.startSlideTimer();
    } else {
      this.close();
      if (window.App) window.App.showToast("✨ Secret Photos completed!");
    }
  },

  prevSlide() {
    if (this.currentSlideIndex > 0) {
      this.renderSlide(this.currentSlideIndex - 1);
      this.startSlideTimer();
    }
  },

  startSlideTimer() {
    this.stopSlideTimer();
    if (!this.storyData || this.storyData.slides.length <= 1) return;
    this.timer = setTimeout(() => {
      if (!this.isPaused) {
        this.nextSlide();
      }
    }, this.slideDurationMs);
  },

  stopSlideTimer() {
    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }
  },

  bindControls() {
    const btnClose = document.getElementById("btnWrappedClose");
    if (btnClose) {
      btnClose.onclick = () => this.close();
    }

    const btnPrev = document.getElementById("btnWrappedPrev");
    if (btnPrev) {
      btnPrev.onclick = () => this.prevSlide();
    }

    const btnNext = document.getElementById("btnWrappedNext");
    if (btnNext) {
      btnNext.onclick = () => this.nextSlide();
    }

    // Keyboard controls
    document.onkeydown = (e) => {
      const modal = document.getElementById("wrappedModal");
      if (modal && !modal.classList.contains("hidden")) {
        if (e.key === "ArrowRight" || e.key === " ") {
          this.nextSlide();
        } else if (e.key === "ArrowLeft") {
          this.prevSlide();
        } else if (e.key === "Escape") {
          this.close();
        }
      }
    };
  },

  bindPhotoUploadControls() {
    const btnAddPhoto = document.getElementById("btnWrappedAddPhoto");
    const photoModal = document.getElementById("wrappedAddPhotoModal");
    const btnClosePhotoModal = document.getElementById("btnCloseWrappedAddPhotoModal");
    const btnCancelDirectPhoto = document.getElementById("btnCancelDirectPhoto");
    const form = document.getElementById("formDirectWrappedPhoto");
    const fileInput = document.getElementById("directWrappedPhotoFile");
    const previewBox = document.getElementById("directPhotoPreviewBox");
    const previewImg = document.getElementById("directPhotoPreviewImg");
    const statusBox = document.getElementById("directPhotoStatus");

    if (!photoModal) return;

    if (btnAddPhoto) {
      btnAddPhoto.onclick = () => {
        this.stopSlideTimer(); // Pause presentation while adding photo
        if (form) form.reset();
        if (previewBox) previewBox.classList.add("hidden");
        if (statusBox) statusBox.classList.add("hidden");
        photoModal.classList.remove("hidden");
        photoModal.style.display = "flex";
      };
    }

    const closeDirectModal = () => {
      photoModal.classList.add("hidden");
      photoModal.style.display = "none";
      this.startSlideTimer();
    };

    if (btnClosePhotoModal) btnClosePhotoModal.onclick = closeDirectModal;
    if (btnCancelDirectPhoto) btnCancelDirectPhoto.onclick = closeDirectModal;

    // Image preview on file selection
    if (fileInput) {
      fileInput.onchange = () => {
        const file = fileInput.files?.[0];
        if (file && previewBox && previewImg) {
          const reader = new FileReader();
          reader.onload = (e) => {
            previewImg.src = e.target.result;
            previewBox.classList.remove("hidden");
          };
          reader.readAsDataURL(file);
        }
      };
    }

    if (!this.photoEventsBound && form) {
      this.photoEventsBound = true;
      form.onsubmit = async (e) => {
        e.preventDefault();
        const file = fileInput?.files?.[0];
        const caption = document.getElementById("directWrappedPhotoCaption")?.value || "";

        if (!file) return;

        if (statusBox) {
          statusBox.className = "form-status";
          statusBox.textContent = "Uploading and saving photo...";
          statusBox.classList.remove("hidden");
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("caption", caption);
        formData.append("slide_id", "moments");

        try {
          await API.wrapped.uploadPhoto(formData);
          if (statusBox) {
            statusBox.className = "form-status success";
            statusBox.textContent = "Photo added successfully!";
          }
          if (window.App) window.App.showToast("📸 Photo added to Secret Vault!");

          // Reload photos payload and re-render
          this.storyData = null;
          this.storyData = await API.wrapped.getStory();
          closeDirectModal();
          this.renderSlide(this.storyData.slides.length - 1); // Jump to the newly added photo!
        } catch (err) {
          if (statusBox) {
            statusBox.className = "form-status error";
            statusBox.textContent = `Upload failed: ${err.message}`;
          }
        }
      };
    }
  },

  triggerConfetti() {
    const container = document.getElementById("wrappedConfettiContainer");
    if (!container) return;
    container.innerHTML = "";

    const colors = ["#ec4899", "#f43f5e", "#8b5cf6", "#10b981", "#f59e0b", "#38bdf8"];
    for (let i = 0; i < 35; i++) {
      const el = document.createElement("div");
      el.className = "confetti-piece";
      el.style.left = `${Math.random() * 100}%`;
      el.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
      el.style.animationDelay = `${Math.random() * 0.5}s`;
      el.style.transform = `rotate(${Math.random() * 360}deg)`;
      container.appendChild(el);
    }
  },

  escapeHtml(text) {
    if (!text) return "";
    return text
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  }
};

window.WrappedComponent = WrappedComponent;
