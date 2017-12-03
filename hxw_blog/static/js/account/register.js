/**
 * Created by tony on 17-11-12.
 */
$(function () {
    var btn_register = $("#btn_register");
    var register_form_input = $("#form_register :input");
    bind_auto_submit(register_form_input, btn_register);
    bind_dismiss_msg_container($("#warning_msg"));

    btn_register.click(function (e) {
        var form = $(this).parent('form');
        var username = form.find('[name="username"]').val();
        var email = form.find('[name="email"]').val();
        var password = form.find('[name="password"]').val();
        var confirm_password = form.find('[name="confirm_password"]').val();
        var redirect_url = this.dataset.next;
        
        var reg_username = /^[\w_\u4e00-\u9fa5]{2,32}$/;
        var reg_email = /^([\.a-zA-Z0-9_-])+@([a-zA-Z0-9_-])+(\.[a-zA-Z0-9_-])+/;
        var reg_password = /^[\.\w@_-]{6,32}$/;
        var warning_div = $("#warning_msg");

        if (username == '') {
            var msg = '请输入昵称';
            show_msg(warning_div, msg);
            return false
        }
        else if (!reg_username.test(username)) {
            var msg = '昵称格式有误，请重新输入';
            show_msg(warning_div, msg);
            return false
        }
        else if (email == '') {
            var msg = '请输入邮箱';
            show_msg(warning_div, msg);
            return false
        }
        else if (!reg_email.test(email)) {
            var msg = '邮箱格式有误，请重新输入';
            show_msg(warning_div, msg);
            return false
        }
        else if (password == '' || confirm_password == '') {
            var msg = '请输入密码';
            show_msg(warning_div, msg);
            return false
        }
        else if (!reg_password.test(password)) {
            var msg = '密码格式有误，请重新输入';
            show_msg(warning_div, msg);
            return false
        }
        else if (password != confirm_password) {
            var msg = '密码输入不一致';
            show_msg(warning_div, msg);
            return false
        }

        $.post(
            register_url,
            {
                "username": username,
                "email": email,
                "password": password,
                "confirm_password": confirm_password,
                "redirect_url": redirect_url
            },
            function (data) {
                if (data.code == 200) {
                    layer.msg(data.msg, {time: 1000});
                    window.location.href = data.redirect_url;
                }
                else {
                    show_msg(warning_div, data.msg);
                    return false
                }
            }
        );
    });
});