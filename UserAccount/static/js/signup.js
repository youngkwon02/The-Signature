
function emailCheck() {
    console.log("Eamil Check clicked");
    var request_email = document.querySelector("#emailInput").value;
    console.log("Target value: " + request_email );
    let returnValue = false; //이미 존재하면 false를 리턴.
    $.ajax({
        url: 'emailcheck/',
        type: 'GET',
        async: false,
        data: {'request_email': request_email},
        success: function(data) {
            console.log("Already exist: " + data);
            if(data === 'Exist') {
                returnValue = false;
            } else {
                returnValue = true;
            }
        }
    })
    return returnValue;
}

function fillEmailCheckResult() {
    let result_holder = document.querySelector('#checkResult');
    var request_email = document.querySelector("#emailInput").value;
//    console.log("printing",request_email);
    if(emailCheck() === false) {
        result_holder.innerHTML = '이미 가입된 이메일입니다.';
        result_holder.style.setProperty('color', '#f8756c');
        pwCheck(); // Join Button activation check
    } else {
        if (request_email){
        result_holder.innerHTML = '사용 가능한 이메일입니다.';
        result_holder.style.setProperty('color', '#6ca4f8');
        pwCheck(); // Join Button activation check
        }
        else{
        result_holder.innerHTML = '이메일을 입력해주세요.';
        result_holder.style.setProperty('color', '#f8756c');
        pwCheck(); // Join Button activation check
        }

    }
}

function pwCheck(){
    var pw = document.getElementById('pw1').value;
    var pattern1 = /[0-9]/;
    var pattern2 = /[a-zA-Z]/;
    var pattern3 = /[~!@\#$%<>^&*]/;
    if (!pattern1.test(pw)||!pattern2.test(pw)||!pattern3.test(pw)||pw.length < 6) {
        inactiveJoin();
        return '비밀번호 조건을 만족해주세요.';
    } else{
        document.getElementById('lenCheck').innerHTML='';
        if (document.getElementById('pw2').value!=''){
            if(document.getElementById('pw1').value==document.getElementById('pw2').value) {
                if (emailCheck()) {
                    console.log("Active");
                    activeJoin();
                } else {
                    inactiveJoin();
                }
                return '비밀번호가 일치합니다.';
            }
            else {
                inactiveJoin();
                return '비밀번호가 일치하지 않습니다.';
            }
        }
    }
}

function fillPwCheckResult() {
    if (pwCheck() === '비밀번호 조건을 만족해주세요.') {
        document.getElementById('lenCheck').innerHTML='비밀번호 조건을 만족해주세요.';
        document.getElementById('pwCheck').innerHTML='';
        document.getElementById('lenCheck').style.color='#f8756c';
        inactiveJoin();
    } else{
        document.getElementById('lenCheck').innerHTML='';

        if (document.getElementById('pw2').value!=''){
            if(document.getElementById('pw1').value==document.getElementById('pw2').value) {
                document.getElementById('pwCheck').innerHTML='비밀번호가 일치합니다.';
                document.getElementById('pwCheck').style.color='#6ca4f8';
                if (emailCheck()) {
                    console.log("Active");
                    activeJoin();
                } else {
                    inactiveJoin();
                }
            }
            else {
                document.getElementById('pwCheck').innerHTML='비밀번호가 일치하지 않습니다.';
                document.getElementById('pwCheck').style.color='#f8756c';
                console.log("Inactive");
                inactiveJoin();
            }
        }
    }
}

function inactiveJoin(){
    $(".joinBtn").prop("disabled", true);
    $(".joinBtn").css("background-color", "#c7c7c2");
    $(".joinBtn").css("color", "white");
}

function activeJoin(){
    $(".joinBtn").prop("disabled", false);
    $(".joinBtn").css("background-color", "#6b6351");


    const element = document.querySelector("#joinBtn");
    element.addEventListener("mouseover", event => {
        // console.log("Mouse in");
        $(".joinBtn").css("background-color", "#a39a86");
        $(".joinBtn").css("color", "white");
    
        });
    
        element.addEventListener("mouseout", event => {
        // console.log("Mouse out");
        $(".joinBtn").css("background-color", "#6b6351");
        $(".joinBtn").css("color", "black");
    
        });
}

function emailWrite(){
    inactiveJoin();
}


//function (){
//    console.log("hi ",{{ request.session.email_sent }});
//    if({{ request.session.email_sent }}){
//    alert({{ request.session.email_sent }});
//    }
//}