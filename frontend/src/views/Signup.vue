<template>
    <h1>Signup</h1>

    <label for="username"> username </label>
    <input id="username" v-model="username" type="text">

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
            username: ""
        };
    },
    
    methods: {
        async login(){
            const form_data = {
                email :  this.email,
                password : this.password,
                username: this.username
                }
  
            const response = await fetch("http://127.0.0.1:5000/signup", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify(form_data)
            });

            const resp = await response.json()
            alert(JSON.stringify(resp))
            if (resp.msg == "user created correctly") {
                alert("user created")
                this.$router.push({name: 'login'})
            } else {
                alert("user not created")
            }

            console.log(resp)
            console.log(response)
            this.$router.push('/login')
        }
    }

}
</script>