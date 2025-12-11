document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("loginForm");
    const username = document.getElementById("username");
    const password = document.getElementById("password");
    const toggle = document.getElementById("togglePassword");

    // Prevent JS errors
    if (!form || !username || !password || !toggle) return;

    // Password toggle
    toggle.addEventListener("click", () => {
        const isHidden = password.type === "password";
        password.type = isHidden ? "text" : "password";
        toggle.textContent = isHidden ? "👁️‍🗨️" : "👁️";
    });

    // Mark input error
    function markError(field) {
        field.classList.add("error-input");
        field.parentElement.classList.add("shake");
        setTimeout(() => field.parentElement.classList.remove("shake"), 400);
    }

    // Remove error on typing
    document.querySelectorAll("input").forEach(el => {
        el.addEventListener("input", () => el.classList.remove("error-input"));
    });

    // Validation
    form.addEventListener("submit", (e) => {
        let valid = true;

        if (username.value.trim() === "") {
            markError(username);
            valid = false;
        }
        if (password.value.trim() === "") {
            markError(password);
            valid = false;
        }

        if (!valid) e.preventDefault();
    });
});
