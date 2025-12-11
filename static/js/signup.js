document.addEventListener("DOMContentLoaded", () => {

    const form = document.getElementById("signupForm");

    const password = document.getElementById("password");
    const confirmPassword = document.getElementById("confirm_password");
    const phone = document.getElementById("phone");

    const togglePass = document.getElementById("togglePassword");
    const toggleConfirm = document.getElementById("toggleConfirmPassword");

    // =========================
    //  Show / Hide Password
    // =========================
    const toggleVisibility = (input, icon) => {
        if (input.type === "password") {
            input.type = "text";
            icon.classList.remove("fa-eye-slash");
            icon.classList.add("fa-eye");
        } else {
            input.type = "password";
            icon.classList.remove("fa-eye");
            icon.classList.add("fa-eye-slash");
        }
    };

    togglePass?.addEventListener("click", () => {
        toggleVisibility(password, togglePass);
    });

    toggleConfirm?.addEventListener("click", () => {
        toggleVisibility(confirmPassword, toggleConfirm);
    });

    // =========================
    //  FORM SUBMIT VALIDATIONS
    // =========================
    form.addEventListener("submit", (e) => {

        // 1) Password match
        if (password.value !== confirmPassword.value) {
            e.preventDefault();
            alert("Passwords do not match!");
            confirmPassword.style.border = "2px solid red";
            return;
        }
        confirmPassword.style.border = "";

        // 2) Phone validation (optional)
        if (phone.value.trim() !== "" && phone.value.length !== 10) {
            e.preventDefault();
            alert("Phone number must be 10 digits.");
            phone.style.border = "2px solid red";
            return;
        }
        phone.style.border = "";

    });

});
