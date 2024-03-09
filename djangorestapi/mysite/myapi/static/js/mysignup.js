function checkpassword(str)
{
    var re = /(?=.*\d)(?=.*[a-z])(?=.*[A-Z]).{6,}/;
    return re.test(str);
}

function checkForm(form)
{
  if(form.email.value == "") {
    alert("Error: email id cannot be blank!");
    form.email.focus();
    return false;
  }
  //re = /^\w+$/;
  re=/^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/;
  if(!(form.email.value).match(re)) {
    alert("Error: email must contain only letters, numbers and underscores!");
    form.email.focus();
    return false;
  }
  if(form.pass.value != "" && form.pass.value == form.pass1.value) {
    if(!checkPassword(form.pass1.value)) {
      alert("The password you have entered is not valid!");
      form.pass1.focus();
      return false;
    }
  } else {
    alert("Error: Please check that you've entered and confirmed your password!");
    form.pass1.focus();
    return false;
  }
  return true;
}
