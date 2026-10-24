/**
 * Settings Component
 * - Auto-lock inactivity timeout
 * - Master password change
 * - AES-256-GCM Encrypted Backup Export & Restore
 * - WhatsApp TXT re-import
 * - Nuclear Data Wipe
 */

const SettingsComponent = {
  init() {
    this.bindEvents();
  },

  bindEvents() {
    // 1. Auto-Lock Timeout
    const formAutoLock = document.getElementById("formAutoLock");
    if (formAutoLock) {
      formAutoLock.addEventListener("submit", async (e) => {
        e.preventDefault();
        const timeout = parseInt(document.getElementById("selectLockTimeout")?.value || 15);
        try {
          await API.auth.lockSettings(timeout);
          if (window.App) {
            window.App.inactivityTimeoutMinutes = timeout;
            window.App.resetInactivityTimer();
            window.App.showToast(`Auto-lock timeout set to ${timeout} minutes.`);
          }
        } catch (err) {
          if (window.App) window.App.showToast(`Error: ${err.message}`);
        }
      });
    }

    // 2. Change Password
    const formChangePassword = document.getElementById("formChangePassword");
    const changeStatus = document.getElementById("changePasswordStatus");
    if (formChangePassword) {
      formChangePassword.addEventListener("submit", async (e) => {
        e.preventDefault();
        const currentPass = document.getElementById("currentPasswordInput")?.value;
        const newPass = document.getElementById("newPasswordInput")?.value;

        if (!currentPass || !newPass) return;
        try {
          const res = await API.auth.changePassword(currentPass, newPass);
          API.setToken(res.token);
          if (changeStatus) {
            changeStatus.className = "form-status success";
            changeStatus.textContent = "Master password updated successfully.";
            changeStatus.classList.remove("hidden");
          }
          formChangePassword.reset();
        } catch (err) {
          if (changeStatus) {
            changeStatus.className = "form-status error";
            changeStatus.textContent = err.message;
            changeStatus.classList.remove("hidden");
          }
        }
      });
    }

    // 3. Export Encrypted Backup
    const formExport = document.getElementById("formExportBackup");
    if (formExport) {
      formExport.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pass = document.getElementById("backupPassphraseInput")?.value;
        if (!pass) return;

        try {
          const res = await API.system.exportBackup(pass);
          if (res.blob) {
            const blobUrl = URL.createObjectURL(res.blob);
            const a = document.createElement("a");
            a.href = blobUrl;
            a.download = res.filename || "vinu_bhumi_encrypted_backup.enc";
            document.body.appendChild(a);
            a.click();
            a.remove();
            URL.revokeObjectURL(blobUrl);
            if (window.App) window.App.showToast("Encrypted backup downloaded successfully.");
            formExport.reset();
          }
        } catch (err) {
          if (window.App) window.App.showToast(`Backup error: ${err.message}`);
        }
      });
    }

    // 4. Restore Encrypted Backup
    const formRestore = document.getElementById("formRestoreBackup");
    const restoreStatus = document.getElementById("restoreStatus");
    if (formRestore) {
      formRestore.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("restoreFileInput");
        const pass = document.getElementById("restorePassphraseInput")?.value;
        const file = fileInput?.files?.[0];

        if (!file || !pass) return;

        if (restoreStatus) {
          restoreStatus.className = "form-status";
          restoreStatus.textContent = "Decrypting and restoring archive...";
          restoreStatus.classList.remove("hidden");
        }

        try {
          const res = await API.system.restoreBackup(file, pass);
          if (restoreStatus) {
            restoreStatus.className = "form-status success";
            restoreStatus.textContent = `Restored ${res.restored_messages} messages and ${res.restored_memories} memories!`;
          }
          formRestore.reset();
          if (window.App) window.App.refreshAllViews();
        } catch (err) {
          if (restoreStatus) {
            restoreStatus.className = "form-status error";
            restoreStatus.textContent = `Restore failed: ${err.message}`;
          }
        }
      });
    }

    // 5. Import WhatsApp TXT
    const formImportTxt = document.getElementById("formImportTxt");
    const importStatus = document.getElementById("importTxtStatus");
    if (formImportTxt) {
      formImportTxt.addEventListener("submit", async (e) => {
        e.preventDefault();
        const file = document.getElementById("txtFileInput")?.files?.[0];
        if (!file) return;

        if (importStatus) {
          importStatus.className = "form-status";
          importStatus.textContent = "Parsing and indexing WhatsApp messages...";
          importStatus.classList.remove("hidden");
        }

        try {
          const res = await API.system.importTxt(file);
          if (importStatus) {
            importStatus.className = "form-status success";
            importStatus.textContent = res.message || `Success! Added ${res.imported_count} new messages.`;
          }
          formImportTxt.reset();
          if (window.App) {
            window.App.showToast(`Import complete: ${res.imported_count} new messages added!`);
            await window.App.refreshAllViews();
          }
        } catch (err) {
          if (importStatus) {
            importStatus.className = "form-status error";
            importStatus.textContent = `Import failed: ${err.message}`;
          }
        }
      });
    }

    // 6. Nuclear Wipe Data
    const formWipe = document.getElementById("formWipeData");
    const wipeStatus = document.getElementById("wipeStatus");
    if (formWipe) {
      formWipe.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pass = document.getElementById("wipePasswordConfirm")?.value;
        if (!pass) return;

        const confirmMsg = "Are you ABSOLUTELY sure you want to permanently erase all chat records and memories?";
        if (!confirm(confirmMsg)) return;

        try {
          await API.system.wipeAll(pass);
          API.clearToken();
          alert("All chat records and settings have been completely erased.");
          window.location.reload();
        } catch (err) {
          if (wipeStatus) {
            wipeStatus.className = "form-status error";
            wipeStatus.textContent = err.message;
            wipeStatus.classList.remove("hidden");
          }
        }
      });
    }

    // 7. Wrapped Secret PIN Form
    const formSetPin = document.getElementById("formSetWrappedPin");
    const pinStatus = document.getElementById("statusSetWrappedPin");
    const btnRemovePin = document.getElementById("btnRemoveWrappedPin");

    if (formSetPin) {
      formSetPin.addEventListener("submit", async (e) => {
        e.preventDefault();
        const pin = document.getElementById("wrappedPinInput")?.value || "";
        try {
          const res = await API.wrapped.setPin(pin);
          if (pinStatus) {
            pinStatus.className = "form-status success";
            pinStatus.textContent = res.message || "Secret PIN saved successfully!";
            pinStatus.classList.remove("hidden");
          }
          if (window.App) window.App.showToast(res.message || "Wrapped PIN saved!");
        } catch (err) {
          if (pinStatus) {
            pinStatus.className = "form-status error";
            pinStatus.textContent = err.message || "Failed to set PIN.";
            pinStatus.classList.remove("hidden");
          }
        }
      });
    }

    if (btnRemovePin) {
      btnRemovePin.addEventListener("click", async () => {
        if (!confirm("Are you sure you want to remove the Secret PIN for Wrapped?")) return;
        try {
          const res = await API.wrapped.setPin("");
          const pinInput = document.getElementById("wrappedPinInput");
          if (pinInput) pinInput.value = "";
          if (pinStatus) {
            pinStatus.className = "form-status success";
            pinStatus.textContent = "PIN removed. Wrapped can now be opened directly.";
            pinStatus.classList.remove("hidden");
          }
          if (window.App) window.App.showToast("Wrapped PIN removed.");
        } catch (err) {
          alert(`Error: ${err.message}`);
        }
      });
    }

    // 8. Wrapped Personal Photo Upload Form
    const formUploadPhoto = document.getElementById("formUploadWrappedPhoto");
    const photoUploadStatus = document.getElementById("statusUploadWrappedPhoto");

    if (formUploadPhoto) {
      formUploadPhoto.addEventListener("submit", async (e) => {
        e.preventDefault();
        const fileInput = document.getElementById("wrappedPhotoFileInput");
        const file = fileInput?.files?.[0];
        const caption = document.getElementById("wrappedPhotoCaption")?.value || "";
        const slideId = document.getElementById("wrappedPhotoSlide")?.value || "moments";

        if (!file) return;

        if (photoUploadStatus) {
          photoUploadStatus.className = "form-status";
          photoUploadStatus.textContent = "Uploading and preparing photo for Wrapped...";
          photoUploadStatus.classList.remove("hidden");
        }

        const formData = new FormData();
        formData.append("file", file);
        formData.append("caption", caption);
        formData.append("slide_id", slideId);

        try {
          await API.wrapped.uploadPhoto(formData);
          if (photoUploadStatus) {
            photoUploadStatus.className = "form-status success";
            photoUploadStatus.textContent = "Photo uploaded and added to Wrapped story!";
          }
          formUploadPhoto.reset();
          if (window.App) window.App.showToast("📸 Photo added to Wrapped!");
          await this.loadWrappedPhotos();
          // Invalidate cached story data so next launch includes the new photo
          if (window.WrappedComponent) window.WrappedComponent.storyData = null;
        } catch (err) {
          if (photoUploadStatus) {
            photoUploadStatus.className = "form-status error";
            photoUploadStatus.textContent = `Upload failed: ${err.message}`;
          }
        }
      });
    }

    // Initial load of photos
    this.loadWrappedPhotos();
  },

  async loadWrappedPhotos() {
    const gallery = document.getElementById("wrappedPhotosGallery");
    if (!gallery) return;

    try {
      const photos = await API.wrapped.getPhotos();
      if (!photos || photos.length === 0) {
        gallery.innerHTML = `
          <div style="grid-column: 1 / -1; padding: 1.5rem; text-align: center; color: var(--text-muted); background: var(--bg-surface); border-radius: var(--radius-sm); border: 1px dashed var(--border-color); font-size: 0.85rem;">
            📸 No personal photos added yet. Upload your favorite moments above to see them in your Friendship Wrapped!
          </div>
        `;
        return;
      }

      gallery.innerHTML = photos.map(p => `
        <div class="wrapped-photo-item" style="background: var(--bg-surface); border-radius: 10px; border: 1px solid var(--border-color); overflow: hidden; position: relative; display: flex; flex-direction: column;">
          <img src="${p.url}" alt="${p.caption || 'Photo'}" style="width: 100%; height: 110px; object-fit: cover; display: block;">
          <div style="padding: 0.5rem; font-size: 0.75rem; flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
            <div style="font-weight: 600; color: var(--text-main); line-height: 1.2; word-break: break-word; margin-bottom: 0.25rem;">
              ${p.caption || '<em>Untitled</em>'}
            </div>
            <div style="font-size: 0.68rem; color: var(--text-muted); margin-bottom: 0.5rem;">
              Tag: ${p.slide_id}
            </div>
            <button class="btn btn-sm btn-danger-outline btn-delete-wrapped-photo" data-id="${p.id}" style="width: 100%; padding: 0.25rem; font-size: 0.72rem;">
              🗑️ Delete
            </button>
          </div>
        </div>
      `).join("");

      // Bind delete photo buttons
      gallery.querySelectorAll(".btn-delete-wrapped-photo").forEach(btn => {
        btn.onclick = async () => {
          const id = parseInt(btn.dataset.id);
          if (!confirm("Remove this photo from Wrapped?")) return;
          try {
            await API.wrapped.deletePhoto(id);
            if (window.App) window.App.showToast("Photo deleted.");
            await this.loadWrappedPhotos();
            if (window.WrappedComponent) window.WrappedComponent.storyData = null;
          } catch (err) {
            alert("Error deleting photo: " + err.message);
          }
        };
      });
    } catch (err) {
      console.error("Failed to load wrapped photos:", err);
    }
  }
};
