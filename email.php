<?php

if (isset($_POST['send'])){
    $to = "varun@vsrivastava.com";
    $subject = $_POST['name'];
    $message .= 'Email: ' .$_POST['email'] . "\r\n\n\n";
    $message .= 'Message: ' .$_POST['comments'];

    $success =  mail($to, $subject, $message, "From:".$to);
}

echo $success;

if(isset($success) && $success){
    echo "<h1>Mail sent successfully</h1>";
} else{
    echo "<h1>Mail could not be sent, please send an email to varun@vsrivastava.com</h1>";
}
echo "<a href='/'>Go back</a>";

?>