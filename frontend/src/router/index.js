import { createRouter, createWebHistory } from 'vue-router'
import HelloWorldVue from '../components/HelloWorld.vue'
import Home from '../views/Home.vue'
import Login from '../views/Login.vue'
import Signup from '../views/Signup.vue'


const router = createRouter({
    history: createWebHistory(import.meta.env.BASE_URL),
    routes: [
        {
            path: '/hello',
            name: 'hello',
            component: HelloWorldVue
        },
        {
            path: '/',
            name: 'home',
            component: Home

        },
        {
            path: '/login',
            name: 'login',
            component: Login

        },
        {
            path: '/signup',
            name: 'signup',
            component: Signup

        }

    ]
})

export default router