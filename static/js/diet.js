// Diet Profile Advisor Wizard & Recommendations Logic

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("diet-profile-form");
    const prevBtn = document.getElementById("prev-btn");
    const nextBtn = document.getElementById("next-btn");
    const submitBtn = document.getElementById("submit-btn");
    const steps = document.querySelectorAll(".form-step");
    const bubbles = document.querySelectorAll(".step-bubble");
    const recSection = document.getElementById("recommendations-section");
    const recommendedList = document.getElementById("recommended-list");
    const avoidList = document.getElementById("avoid-list");

    let currentStep = 1;

    // 1. Wizard Step Navigation
    nextBtn.addEventListener("click", () => {
        if (validateStep(currentStep)) {
            // Mark current bubble as completed
            bubbles[currentStep - 1].classList.remove("active");
            bubbles[currentStep - 1].classList.add("completed");
            
            currentStep++;
            
            // Set next bubble active
            bubbles[currentStep - 1].classList.add("active");
            
            updateSteps();
        }
    });

    prevBtn.addEventListener("click", () => {
        // Reset current bubble
        bubbles[currentStep - 1].classList.remove("active");
        
        currentStep--;
        
        // Restore previous bubble to active
        bubbles[currentStep - 1].classList.remove("completed");
        bubbles[currentStep - 1].classList.add("active");
        
        updateSteps();
    });

    function updateSteps() {
        // Show/hide step panels
        steps.forEach((step, index) => {
            if (index + 1 === currentStep) {
                step.classList.add("active");
            } else {
                step.classList.remove("active");
            }
        });

        // Configure Back button visibility
        if (currentStep === 1) {
            prevBtn.style.visibility = "hidden";
        } else {
            prevBtn.style.visibility = "visible";
        }

        // Configure Next vs Submit buttons
        if (currentStep === steps.length) {
            nextBtn.style.display = "none";
            submitBtn.style.display = "inline-block";
        } else {
            nextBtn.style.display = "inline-block";
            submitBtn.style.display = "none";
        }
    }

    function validateStep(stepNum) {
        const stepPanel = steps[stepNum - 1];
        const inputs = stepPanel.querySelectorAll("input[required], select[required]");
        let valid = true;

        inputs.forEach(input => {
            if (!input.checkValidity()) {
                input.reportValidity();
                valid = false;
            }
        });

        return valid;
    }

    // 2. Submit Profile Details & Fetch AI Advisor Recommendations
    form.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        if (!validateStep(currentStep)) return;

        // Collect health condition checkboxes
        const checkedConditions = [];
        const checkboxes = document.querySelectorAll("input[name='conditions']:checked");
        checkboxes.forEach(cb => {
            checkedConditions.push(cb.value);
        });

        const profileData = {
            age: parseInt(document.getElementById("age").value),
            weight: parseFloat(document.getElementById("weight").value),
            height: parseFloat(document.getElementById("height").value),
            lifestyle: document.getElementById("lifestyle").value,
            goal: document.getElementById("goal").value,
            diet_type: document.getElementById("diet_type").value,
            health_conditions: checkedConditions.join(",")
        };

        toggleLoader(true, "Saving health profile details...");

        try {
            // Save health profile
            const profileResponse = await fetch("/api/diet/profile", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(profileData)
            });

            const profileResult = await profileResponse.json();
            if (!profileResponse.ok) {
                throw new Error(profileResult.error || "Failed to save profile.");
            }

            // Update loading text for AI recommendation fetch
            toggleLoader(true, "Consulting AI Dietitian for Amul products...");

            // Fetch Advisor suggestions
            const recResponse = await fetch("/api/diet/recommend", {
                method: "POST",
                headers: { "Content-Type": "application/json" }
            });

            const recResult = await recResponse.json();
            if (!recResponse.ok) {
                throw new Error(recResult.error || "Failed to generate recommendations.");
            }

            displayRecommendations(recResult);
            showAlert("Profile saved & advisor suggestions updated!", "success");

        } catch (err) {
            console.error(err);
            showAlert(err.message || "An error occurred.", "danger");
        } finally {
            toggleLoader(false);
        }
    });

    // 3. Render Recommendation Cards in HTML Grid
    function displayRecommendations(data) {
        recommendedList.innerHTML = "";
        avoidList.innerHTML = "";

        const recommended = data.recommended || [];
        const avoid = data.avoid || [];

        // Populate recommended
        if (recommended.length === 0) {
            recommendedList.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-light); width: 100%;">No recommendation records returned.</div>`;
        } else {
            recommended.forEach(item => {
                const card = createRecommendationCard(item, "recommend");
                recommendedList.appendChild(card);
            });
        }

        // Populate avoid
        if (avoid.length === 0) {
            avoidList.innerHTML = `<div style="text-align: center; padding: 2rem; color: var(--text-light); width: 100%;">No avoidance records returned.</div>`;
        } else {
            avoid.forEach(item => {
                const card = createRecommendationCard(item, "avoid");
                avoidList.appendChild(card);
            });
        }

        // Display results block
        recSection.style.display = "block";
        recSection.scrollIntoView({ behavior: "smooth" });
    }

    function createRecommendationCard(item, verdict) {
        const card = document.createElement("div");
        card.className = "rec-card";

        const badgeClass = verdict === "recommend" ? "recommend" : "avoid";
        const badgeLabel = verdict === "recommend" ? "Recommend" : "Limit/Avoid";

        card.innerHTML = `
            <div class="rec-card-details">
                <h4>${item.product_name}</h4>
                <p class="rec-reason">${item.reason}</p>
                <p class="rec-serving">💡 Serving tip: ${item.suggested_serving || 'Consume in moderation'}</p>
            </div>
            <div class="suitability-badge ${badgeClass}">${badgeLabel}</div>
        `;

        return card;
    }

    // 4. Auto-trigger Recommendation fetching on page load if profile exists
    const hasProfileData = document.getElementById("age").value !== "";
    if (hasProfileData) {
        // Run immediately in background
        (async () => {
            try {
                // Fetch recommendations silently on page load
                const response = await fetch("/api/diet/recommend", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });
                if (response.ok) {
                    const data = await response.json();
                    displayRecommendations(data);
                }
            } catch (e) {
                console.warn("Could not load initial recommendations:", e);
            }
        })();
    }
});
