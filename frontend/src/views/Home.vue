<template>

    <h1>home page</h1>
    <button @click="hello()"> click me </button>

</template>


<script>
export default {

    data() {
        return {

        }
    },

    methods:{
         async fetch_tasks(){
            const token = localStorage.getItem('jwt_token')

            const response = await fetch("http://127.0.0.1:5000/", {
                method: "get",
                headers: {'Authorization': `Bearer  ${token}`},
            });

            resp = await response.json()
            alert(resp.msg)
         }
    },

    mounted(){
        this.fetch_tasks()
    }
}

</script>

