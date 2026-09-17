// Every page under /app/ is behind the login: signed out, it sends you to the form.
if (!localStorage.getItem('auth')) {
  location.replace('/login.html');
}
