// AI Meal Planner Client Logic

document.addEventListener("DOMContentLoaded", () => {
    const form = document.getElementById("meal-planner-form");
    const tableContainer = document.getElementById("planner-table-container");
    const tableBody = document.getElementById("planner-table-body");
    const metaEl = document.getElementById("plan-display-meta");
    const downloadBtn = document.getElementById("download-pdf-btn");

    // 1. Fetch Latest Meal Plan on Page Load
    fetchLatestPlan();

    // 2. Submit Meal Planner Option Settings
    form.addEventListener("submit", async (e) => {
        e.preventDefault();

        const goal = document.getElementById("plan-goal").value;
        const days = parseInt(document.getElementById("plan-days").value);
        const restriction = document.getElementById("plan-restriction").value;

        toggleLoader(true, "AI Dietitian is formulating your meal plan...");

        try {
            const response = await fetch("/api/planner/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ goal, days, restriction })
            });

            const data = await response.json();
            if (!response.ok) {
                throw new Error(data.error || "Failed to generate meal plan.");
            }

            renderMealPlan(data);
            showAlert("New meal plan generated successfully!", "success");

        } catch (err) {
            console.error(err);
            showAlert(err.message || "Could not generate meal plan.", "danger");
        } finally {
            toggleLoader(false);
        }
    });

    // 3. Download / Print PDF Action
    downloadBtn.addEventListener("click", () => {
        window.print();
    });

    // 4. AJAX Latest Plan Loader
    async function fetchLatestPlan() {
        try {
            const response = await fetch("/api/planner/latest");
            if (response.ok) {
                const data = await response.json();
                if (data && data.days) {
                    renderMealPlan(data);
                }
            }
        } catch (e) {
            console.warn("Could not load latest meal plan:", e);
        }
    }

    // 5. Render Plan Data into structured HTML table
    function renderMealPlan(data) {
        tableBody.innerHTML = "";

        // Format goal & restriction names for display
        const goalsMap = {
            "weight_loss": "Weight Loss",
            "muscle_gain": "Muscle Gain",
            "maintenance": "Weight Maintenance",
            "diabetes": "Blood Sugar Management"
        };
        const restrictionMap = {
            "none": "None",
            "vegetarian": "Vegetarian Only",
            "low_sodium": "Low Sodium Target",
            "low_fat": "Low Fat Target"
        };

        const goalName = goalsMap[data.goal] || data.goal || "Healthy Diet";
        const restrictionName = restrictionMap[data.restriction] || data.restriction || "None";
        const totalDays = data.days.length;

        metaEl.textContent = `Goal: ${goalName} | Restriction: ${restrictionName} | Duration: ${totalDays} Days`;

        // Render rows
        data.days.forEach(dayInfo => {
            const row = document.createElement("tr");

            // Targets and daily totals
            const targets = data.targets || { calories: 2000, protein: 100, carbs: 250, fat: 65 };
            const totals = dayInfo.totals || { calories: 0, protein: 0, fat: 0, carbs: 0 };

            const calPct = targets.calories > 0 ? Math.min(100, (totals.calories / targets.calories) * 100) : 0;
            const protPct = targets.protein > 0 ? Math.min(100, (totals.protein / targets.protein) * 100) : 0;
            const carbPct = targets.carbs > 0 ? Math.min(100, (totals.carbs / targets.carbs) * 100) : 0;
            const fatPct = targets.fat > 0 ? Math.min(100, (totals.fat / targets.fat) * 100) : 0;

            // Day title cell
            const dayCell = document.createElement("td");
            dayCell.className = "planner-day-col";
            dayCell.style.width = "180px"; // Give it slightly more room for progress bars
            dayCell.innerHTML = `
                <div style="font-weight: 700; font-size: 1.1rem; color: var(--primary-color); margin-bottom: 0.8rem; font-family: 'Poppins', sans-serif;">${dayInfo.day}</div>
                <div class="day-progress-container" style="display: flex; flex-direction: column; gap: 8px; font-size: 0.72rem; text-align: left; font-weight: normal; color: var(--text-secondary); line-height: 1.2;">
                    <!-- Calories -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span><strong>Cal:</strong> ${totals.calories}</span>
                            <span style="color: var(--text-light); font-size: 0.65rem;">/ ${targets.calories} kcal</span>
                        </div>
                        <div style="background: var(--bg-alt); height: 5px; border-radius: 3px; overflow: hidden;">
                            <div class="progress-fill-animate" style="background: var(--primary-color); --target-width: ${calPct}%; height: 100%; border-radius: 3px; width: 0;"></div>
                        </div>
                    </div>
                    <!-- Protein -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span><strong>Prot:</strong> ${totals.protein}g</span>
                            <span style="color: var(--text-light); font-size: 0.65rem;">/ ${targets.protein}g</span>
                        </div>
                        <div style="background: var(--bg-alt); height: 5px; border-radius: 3px; overflow: hidden;">
                            <div class="progress-fill-animate" style="background: var(--grade-b); --target-width: ${protPct}%; height: 100%; border-radius: 3px; width: 0;"></div>
                        </div>
                    </div>
                    <!-- Carbs -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span><strong>Carb:</strong> ${totals.carbs}g</span>
                            <span style="color: var(--text-light); font-size: 0.65rem;">/ ${targets.carbs}g</span>
                        </div>
                        <div style="background: var(--bg-alt); height: 5px; border-radius: 3px; overflow: hidden;">
                            <div class="progress-fill-animate" style="background: #3498db; --target-width: ${carbPct}%; height: 100%; border-radius: 3px; width: 0;"></div>
                        </div>
                    </div>
                    <!-- Fat -->
                    <div>
                        <div style="display: flex; justify-content: space-between; margin-bottom: 2px;">
                            <span><strong>Fat:</strong> ${totals.fat}g</span>
                            <span style="color: var(--text-light); font-size: 0.65rem;">/ ${targets.fat}g</span>
                        </div>
                        <div style="background: var(--bg-alt); height: 5px; border-radius: 3px; overflow: hidden;">
                            <div class="progress-fill-animate" style="background: #f1c40f; --target-width: ${fatPct}%; height: 100%; border-radius: 3px; width: 0;"></div>
                        </div>
                    </div>
                </div>
            `;
            row.appendChild(dayCell);

            // Meal types to loop
            const mealTypes = ["breakfast", "lunch", "dinner", "snack"];
            mealTypes.forEach(mealKey => {
                const mealCell = document.createElement("td");
                const mealData = dayInfo.meals[mealKey] || {};

                const prodName = mealData.product || "Amul Option";
                const qty = mealData.quantity || "1 portion";
                const tip = mealData.tip || "Enjoy fresh";
                const recipe = mealData.recipe; // optional JSON string

                let recipeHtml = "";
                if (recipe) {
                    let parsedRecipe = null;
                    if (typeof recipe === "object" && recipe !== null) {
                        parsedRecipe = recipe;
                    } else if (typeof recipe === "string") {
                        try {
                            parsedRecipe = JSON.parse(recipe);
                        } catch (e) {
                            // Try to clean/parse
                        }
                    }

                    if (Array.isArray(parsedRecipe)) {
                        parsedRecipe = parsedRecipe[0];
                    }

                    if (parsedRecipe && parsedRecipe.title) {
                        const rawJsonEscaped = encodeURIComponent(JSON.stringify(parsedRecipe));
                        recipeHtml = `
                            <div class="meal-recipe-box" onclick="openRecipeModal('${rawJsonEscaped}')">
                                <div class="recipe-header">
                                    <span class="recipe-badge">Recipe</span>
                                    <strong class="recipe-title" title="${parsedRecipe.title}">${parsedRecipe.title}</strong>
                                </div>
                                <span class="recipe-action">Click to view ↗</span>
                            </div>
                        `;
                    }
                }

                mealCell.innerHTML = `
                    <div class="meal-block">
                        <span class="meal-title">${mealKey}</span>
                        <span class="meal-product">${prodName}</span>
                        <span class="meal-qty">${qty}</span>
                        <span class="meal-tip">${tip}</span>
                        ${recipeHtml}
                    </div>
                `;
                row.appendChild(mealCell);
            });

            tableBody.appendChild(row);
        });

        // Make visible and scroll
        tableContainer.style.display = "block";
        tableContainer.scrollIntoView({ behavior: "smooth" });
    }
});

window.openRecipeModal = function(escapedJson) {
    const recipe = JSON.parse(decodeURIComponent(escapedJson));
    const modal = document.getElementById("recipe-modal");
    const titleEl = document.getElementById("modal-recipe-title");
    const bodyEl = document.getElementById("modal-recipe-body");

    titleEl.textContent = recipe.title;
    bodyEl.innerHTML = "";

    const ingBox = document.createElement("div");
    ingBox.style.marginBottom = "1.2rem";
    ingBox.innerHTML = `<h4 style="margin-bottom: 0.5rem; color: var(--text-primary); font-family: 'Poppins', sans-serif;">Ingredients:</h4>`;
    const ingList = document.createElement("ul");
    ingList.style.paddingLeft = "1.2rem";
    recipe.ingredients.forEach(i => {
        const li = document.createElement("li");
        li.textContent = i;
        li.style.marginBottom = "0.3rem";
        ingList.appendChild(li);
    });
    ingBox.appendChild(ingList);
    bodyEl.appendChild(ingBox);

    const stepsBox = document.createElement("div");
    stepsBox.innerHTML = `<h4 style="margin-bottom: 0.5rem; color: var(--text-primary); font-family: 'Poppins', sans-serif;">Instructions:</h4>`;
    const stepsList = document.createElement("ol");
    stepsList.style.paddingLeft = "1.2rem";
    recipe.steps.forEach(s => {
        const li = document.createElement("li");
        li.textContent = s;
        li.style.marginBottom = "0.5rem";
        stepsList.appendChild(li);
    });
    stepsBox.appendChild(stepsList);
    bodyEl.appendChild(stepsBox);

    modal.style.display = "flex";
};

window.closeRecipeModal = function() {
    document.getElementById("recipe-modal").style.display = "none";
};

// Close modal on clicking outside
document.getElementById("recipe-modal").addEventListener("click", (e) => {
    if (e.target.id === "recipe-modal") {
        window.closeRecipeModal();
    }
});
