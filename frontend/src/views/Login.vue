<template>
    <h1>Login</h1>

    <label for="email"> email </label>
    <input id="email" v-model="email" type="text">

    <label for="password"> password </label>
    <input id="password" v-model="password" type="text">

    <button @click="login()"> submit </button>

</template>


<script>
export default{
    data(){
        return {
            email: "",
            password: "",
        };
    },
    
    methods: {
        async login(){
            const form_data = {
                email :  this.email,
                password : this.password
                }
  
            const response = await fetch("http://127.0.0.1:5000/login", {
                method: "POST",
                headers: { "Content-Type": "application/json" },

                body: JSON.stringify(form_data)
            });

            const resp = await response.json()
            alert(JSON.stringify(resp))
            
            localStorage.setItem('jwt_token', resp.token)

            if (resp.role == "admin") {
                this.$router.push('/admin')
            } else if (resp.role == "employee") {
            this.$router.push('/')
            }
        }
    }

}
</script>