// Tesla Dashboard JavaScript - Interactive Features

class TeslaDashboard {
  constructor() {
    this.init();
    this.setupEventListeners();
    this.requestNotificationPermission();
    this.startAutoRefresh();
  }

  init() {
    this.refreshBtn = document.getElementById("refreshBtn");
    this.loadingOverlay = document.getElementById("loadingOverlay");
    this.toast = document.getElementById("toast");
    this.lastUpdatedElement = document.getElementById("lastUpdated");
    this.vinElement = document.getElementById("vinNumber");
    this.languageSelect = document.getElementById("languageSelect");

    // Store current VIN for comparison
    this.currentVIN = this.vinElement ? this.vinElement.dataset.vin : null;

    // Format initial timestamp
    this.formatTimestamp();
  }

  async requestNotificationPermission() {
    if ("Notification" in window) {
      if (Notification.permission === "default") {
        try {
          const permission = await Notification.requestPermission();
          if (permission === "granted") {
            this.showToast(
              "🔔 Notifications enabled! You'll be notified when your VIN is assigned.",
              "success"
            );
          }
        } catch (error) {
          console.log("Notification permission request failed:", error);
        }
      }
    }
  }

  setupEventListeners() {
    // Refresh button click
    if (this.refreshBtn) {
      this.refreshBtn.addEventListener("click", () => this.refreshData());
    }

    // Language switcher
    if (this.languageSelect) {
      this.languageSelect.addEventListener("change", (e) => {
        this.changeLanguage(e.target.value);
      });
    }

    // Keyboard shortcuts
    document.addEventListener("keydown", (e) => {
      if (e.ctrlKey || e.metaKey) {
        switch (e.key) {
          case "r":
            e.preventDefault();
            this.refreshData();
            break;
        }
      }
    });

    // Auto-hide toast after 5 seconds
    if (this.toast) {
      this.toast.addEventListener("transitionend", (e) => {
        if (e.target === this.toast && !this.toast.classList.contains("show")) {
          this.toast.style.display = "none";
        }
      });
    }
  }

  async refreshData() {
    try {
      this.showLoading(true);
      this.setRefreshButtonState(true);

      const response = await fetch("/api/refresh", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
      });

      const result = await response.json();

      if (result.success) {
        this.showToast(result.message, "success");

        // Update the page with new data
        if (result.data) {
          await this.updateDashboard(result.data);
        } else {
          // Reload the page to show updated data
          setTimeout(() => {
            window.location.reload();
          }, 1500);
        }
      } else {
        this.showToast(`Error: ${result.error}`, "error");
      }
    } catch (error) {
      console.error("Refresh error:", error);
      this.showToast("Failed to refresh data. Please try again.", "error");
    } finally {
      this.showLoading(false);
      this.setRefreshButtonState(false);
    }
  }

  async updateDashboard(data) {
    // Update timestamp
    if (this.lastUpdatedElement && data.last_updated) {
      this.lastUpdatedElement.textContent = this.formatDate(
        new Date(data.last_updated)
      );
    }

    // Check for VIN updates
    this.checkVINUpdate(data.orders);

    // Update interesting facts
    this.updateFacts(data.facts);

    // Update progress indicators
    this.updateProgress(data.orders);

    // Update task status
    this.updateTaskStatus(data.orders);
  }

  checkVINUpdate(orders) {
    if (!orders || orders.length === 0) return;

    const order = orders[0];
    const newVIN = order.basic_info.vin;

    // Check if VIN changed from "Not assigned" to actual VIN
    if (
      this.currentVIN &&
      (this.currentVIN === "Not assigned" || this.currentVIN === "N/A") &&
      newVIN &&
      newVIN !== "Not assigned" &&
      newVIN !== "N/A"
    ) {
      // Show browser notification
      this.showVINNotification(newVIN);

      // Update VIN display
      if (this.vinElement) {
        this.vinElement.textContent = newVIN;
        this.vinElement.dataset.vin = newVIN;

        // Add highlight animation
        this.vinElement.style.backgroundColor = "#10b981";
        this.vinElement.style.color = "white";
        this.vinElement.style.padding = "4px 8px";
        this.vinElement.style.borderRadius = "6px";
        this.vinElement.style.transition = "all 0.3s ease";

        setTimeout(() => {
          this.vinElement.style.backgroundColor = "transparent";
          this.vinElement.style.color = "inherit";
          this.vinElement.style.padding = "0";
        }, 3000);
      }

      // Update stored VIN
      this.currentVIN = newVIN;

      // Show success toast
      this.showToast(`🎉 Your VIN has been assigned: ${newVIN}`, "success");
    } else if (newVIN && newVIN !== this.currentVIN) {
      // Update VIN display for any other changes
      if (this.vinElement) {
        this.vinElement.textContent = newVIN;
        this.vinElement.dataset.vin = newVIN;
      }
      this.currentVIN = newVIN;
    }
  }

  showVINNotification(vin) {
    if ("Notification" in window && Notification.permission === "granted") {
      try {
        const notification = new Notification("🚗 Tesla VIN Assigned!", {
          body: `Your VIN is now available: ${vin}`,
          icon: "/static/favicon.ico", // You can add a Tesla icon here
          badge: "/static/favicon.ico",
          tag: "vin-update",
          requireInteraction: true,
          actions: [
            {
              action: "view",
              title: "View Dashboard",
            },
          ],
        });

        notification.onclick = () => {
          window.focus();
          notification.close();
        };

        // Auto-close after 10 seconds
        setTimeout(() => {
          notification.close();
        }, 10000);
      } catch (error) {
        console.log("Failed to show notification:", error);
      }
    }
  }

  updateFacts(facts) {
    const factsGrid = document.querySelector(".facts-grid");
    if (factsGrid && facts) {
      factsGrid.innerHTML = "";
      facts.forEach((fact) => {
        const factElement = document.createElement("div");
        factElement.className = "fact-item";
        factElement.textContent = fact;
        factsGrid.appendChild(factElement);
      });
    }
  }

  updateProgress(orders) {
    if (!orders || orders.length === 0) return;

    const order = orders[0]; // Assuming single order for now
    const taskStatus = order.task_status;

    if (taskStatus) {
      const completedTasks = Object.values(taskStatus).filter(
        (task) => task.complete
      ).length;
      const totalTasks = Object.values(taskStatus).length;
      const progressPct =
        totalTasks > 0 ? (completedTasks / totalTasks) * 100 : 0;

      // Update progress circle
      const progressRingFill = document.querySelector(".progress-ring-fill");
      const progressText = document.querySelector(".progress-text");

      if (progressRingFill && progressText) {
        const circumference = 2 * Math.PI * 34; // radius = 34
        const offset = circumference * (1 - progressPct / 100);

        progressRingFill.style.strokeDashoffset = offset;
        progressText.textContent = `${Math.round(progressPct)}%`;
      }

      // Update progress text
      const progressTextElement = document.querySelector(".progress-card p");
      if (progressTextElement) {
        progressTextElement.textContent = `${completedTasks}/${totalTasks} tasks completed`;
      }
    }
  }

  updateTaskStatus(orders) {
    if (!orders || orders.length === 0) return;

    const order = orders[0];
    const taskStatus = order.task_status;

    if (taskStatus) {
      Object.entries(taskStatus).forEach(([taskId, task]) => {
        const taskElements = document.querySelectorAll(".task-item");

        taskElements.forEach((element) => {
          const taskName = element.querySelector("h4").textContent;
          if (taskName === task.name) {
            // Update task completion status
            element.className = `task-item ${
              task.complete ? "completed" : "pending"
            }`;

            // Update icon
            const icon = element.querySelector(".task-icon i");
            if (icon) {
              icon.className = task.complete
                ? "fas fa-check-circle"
                : task.enabled
                ? "fas fa-clock"
                : "fas fa-circle";
            }

            // Update status text
            const statusElement = element.querySelector(".task-status");
            if (statusElement) {
              statusElement.textContent =
                task.status !== "N/A" ? task.status : "Pending";
            }
          }
        });
      });
    }
  }

  showLoading(show) {
    if (this.loadingOverlay) {
      this.loadingOverlay.style.display = show ? "flex" : "none";
    }
  }

  setRefreshButtonState(loading) {
    if (this.refreshBtn) {
      this.refreshBtn.disabled = loading;
      this.refreshBtn.classList.toggle("loading", loading);

      const icon = this.refreshBtn.querySelector("i");
      if (icon) {
        icon.style.animation = loading ? "spin 1s linear infinite" : "none";
      }
    }
  }

  showToast(message, type = "success") {
    if (!this.toast) return;

    const toastMessage = document.getElementById("toastMessage");
    const toastIcon = this.toast.querySelector("i");

    if (toastMessage) {
      toastMessage.textContent = message;
    }

    // Update toast appearance based on type
    this.toast.className = `toast toast-${type}`;

    if (toastIcon) {
      toastIcon.className =
        type === "success"
          ? "fas fa-check-circle"
          : "fas fa-exclamation-triangle";
    }

    // Show toast
    this.toast.style.display = "block";
    setTimeout(() => {
      this.toast.classList.add("show");
    }, 100);

    // Hide toast after 5 seconds
    setTimeout(() => {
      this.hideToast();
    }, 5000);
  }

  hideToast() {
    if (this.toast) {
      this.toast.classList.remove("show");
    }
  }

  formatTimestamp() {
    if (this.lastUpdatedElement) {
      const timestamp = this.lastUpdatedElement.textContent;
      if (timestamp && timestamp !== "None") {
        try {
          const date = new Date(timestamp);
          this.lastUpdatedElement.textContent = this.formatDate(date);
        } catch (error) {
          console.warn("Could not parse timestamp:", timestamp);
        }
      }
    }
  }

  formatDate(date) {
    const now = new Date();
    const diffInSeconds = Math.floor((now - date) / 1000);

    if (diffInSeconds < 60) {
      return "Just now";
    } else if (diffInSeconds < 3600) {
      const minutes = Math.floor(diffInSeconds / 60);
      return `${minutes} minute${minutes > 1 ? "s" : ""} ago`;
    } else if (diffInSeconds < 86400) {
      const hours = Math.floor(diffInSeconds / 3600);
      return `${hours} hour${hours > 1 ? "s" : ""} ago`;
    } else {
      return (
        date.toLocaleDateString() +
        " " +
        date.toLocaleTimeString([], {
          hour: "2-digit",
          minute: "2-digit",
        })
      );
    }
  }

  startAutoRefresh() {
    // Auto-refresh every 5 minutes
    console.log("🔄 Auto-refresh enabled: every 5 minutes");
    setInterval(() => {
      console.log("🔄 Auto-refreshing Tesla order data...");
      this.refreshData();
    }, 5 * 60 * 1000); // 5 minutes in milliseconds
  }

  // Utility method to check connection status
  async checkConnection() {
    try {
      const response = await fetch("/health");
      return response.ok;
    } catch {
      return false;
    }
  }

  changeLanguage(language) {
    // Show loading to indicate language change is happening
    this.showLoading(true);
    
    // Redirect to set language endpoint
    window.location.href = `/set_language/${language}`;
  }
}

// Animation utilities
class AnimationUtils {
  static animateValue(element, start, end, duration = 1000) {
    const startTime = performance.now();
    const change = end - start;

    function updateValue(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      // Easing function (ease-out)
      const easeOut = 1 - Math.pow(1 - progress, 3);
      const current = start + change * easeOut;

      element.textContent = Math.round(current);

      if (progress < 1) {
        requestAnimationFrame(updateValue);
      }
    }

    requestAnimationFrame(updateValue);
  }

  static fadeIn(element, duration = 300) {
    element.style.opacity = "0";
    element.style.display = "block";

    const startTime = performance.now();

    function animate(currentTime) {
      const elapsed = currentTime - startTime;
      const progress = Math.min(elapsed / duration, 1);

      element.style.opacity = progress;

      if (progress < 1) {
        requestAnimationFrame(animate);
      }
    }

    requestAnimationFrame(animate);
  }

  static slideIn(element, direction = "up", duration = 300) {
    const transforms = {
      up: "translateY(20px)",
      down: "translateY(-20px)",
      left: "translateX(20px)",
      right: "translateX(-20px)",
    };

    element.style.transform = transforms[direction];
    element.style.opacity = "0";
    element.style.transition = `transform ${duration}ms ease, opacity ${duration}ms ease`;

    setTimeout(() => {
      element.style.transform = "translateY(0)";
      element.style.opacity = "1";
    }, 10);
  }
}

// Progress bar animation
class ProgressBar {
  constructor(element, value, maxValue = 100) {
    this.element = element;
    this.value = value;
    this.maxValue = maxValue;
    this.animate();
  }

  animate() {
    const percentage = (this.value / this.maxValue) * 100;
    const circumference = 2 * Math.PI * 34; // radius = 34
    const offset = circumference * (1 - percentage / 100);

    // Animate the stroke-dashoffset
    this.element.style.transition = "stroke-dashoffset 1.5s ease-in-out";
    this.element.style.strokeDashoffset = offset;
  }
}

// Initialize dashboard when DOM is loaded
document.addEventListener("DOMContentLoaded", () => {
  const dashboard = new TeslaDashboard();

  // Animate progress rings on load
  const progressRings = document.querySelectorAll(".progress-ring-fill");
  progressRings.forEach((ring) => {
    const circumference = 2 * Math.PI * 34;
    const currentOffset = ring.style.strokeDashoffset || circumference;
    ring.style.strokeDashoffset = circumference;

    setTimeout(() => {
      ring.style.transition = "stroke-dashoffset 1.5s ease-in-out";
      ring.style.strokeDashoffset = currentOffset;
    }, 500);
  });

  // Animate cards on load
  const cards = document.querySelectorAll(".card");
  cards.forEach((card, index) => {
    card.style.opacity = "0";
    card.style.transform = "translateY(20px)";

    setTimeout(() => {
      AnimationUtils.slideIn(card, "up", 300);
    }, index * 100);
  });
});

// Export for global access
window.TeslaDashboard = TeslaDashboard;
