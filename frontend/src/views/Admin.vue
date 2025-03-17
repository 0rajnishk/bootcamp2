<template>

    <h1>Admin Dashboard</h1>


    <h2>pending users</h2>
    <ul>
        <li v-for="user in pending_users">
            <p>email: {{ user.email }} </p>
            <p>username: {{ user.username }} </p>
            <p>status: {{ user.is_approved }} </p>
            <p>role: {{ user.role }} </p>
            <button @click="reject_user(user.id)"> reject</button>
            <button @click="approve_user(user.id)"> approve</button>
        </li>
    </ul>

    <!-- <button @click="toggle_task()"> add task </button>

    <div v-if="task_form" >
        <h2>add task form</h2>
        <label for="task_name"> task name </label>
        <input id="task_name" v-model="task.task_name" type="text">

        <label for="task_description"> task description </label>
        <input id="task_description" v-model="task.task_description" type="text">

        <label for="deadline"> deadline </label>
        <input id="deadline" v-model="task.deadline" type="text">
        
        <button @click="add_task()"> add task </button>
    </div> -->


</template>


<script>
export default {

    data() {
        return {
            pending_users: [],
            // task_form: false,
            // task: {
            //     task_name: "",
            //     task_description: "",
            //     deadline: ""
            // }
        }
    },



    methods: {
        async fetch_pending_users() {
            const token = localStorage.getItem('jwt_token')

            const response = await fetch("http://127.0.0.1:5000/users/pending", {
                method: "get",
                headers: { 'Authorization': `Bearer  ${token}` },
            });

            const resp = await response.json()
            alert(JSON.stringify(resp))
            this.pending_users = resp
        },
        async reject_user(user_id) {
            const token = localStorage.getItem('jwt_token')

            const response = await fetch(`http://127.0.0.1:5000/users/${user_id}/reject`, {
                method: "delete",
                headers: { 'Authorization': `Bearer  ${token}` },
            });

            const resp = await response.json()
            if (resp.message == 'User rejected and removed') {
                alert('user rejected successfully')
                this.fetch_pending_users()
            } else {
                alert('user not rejected')
            }
        },
        async approve_user(user_id) {
            const token = localStorage.getItem('jwt_token')

            const response = await fetch(`http://127.0.0.1:5000/users/${user_id}/approve`, {
                method: "put",
                headers: { 'Authorization': `Bearer  ${token}` },
            });

            const resp = await response.json()
            alert(resp.message)

            this.fetch_pending_users()
        },
        // async add_task() {
        //     const token = localStorage.getItem('jwt_token')

        //     const response = await fetch("http://127.0.0.1:5000/add_task", {
        //         method: "post",
        //         headers: { 'Authorization': `Bearer  ${token}` },
        //         body: JSON.stringify({ task: "task1" })
        //     });

        //     const resp = await response.json()
        //     if (resp.msg == 'task added') {
        //         alert('task added')
        //     } else {
        //         alert('task not added')
        //     }
        // },

        // toggle_task() {
        //     this.task_form = !this.task_form
        // }
    },

    mounted() {
        this.fetch_pending_users()
    }
}

</script>
