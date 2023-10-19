<template>
	<nav class="px-2 py-4 flex flex-col gap-1" v-if="currentRoute">
		<ion-menu-toggle auto-hide="false" v-for="item in menuItems" :key="item.title">
			<router-link
				:to="item.route"
				:class="[
					item.current
						? 'bg-gray-200 font-bold text-gray-800'
						: 'text-gray-700 font-normal hover:bg-gray-100 hover:text-gray-900',
					'flex flex-row rounded gap-3 flex-start py-3 px-2 items-center text-sm',
				]"
			>
				<FeatherIcon :name="item.icon" class="h-5 w-5" />
				<div>{{ item.title }}</div>
			</router-link>
		</ion-menu-toggle>
	</nav>
</template>

<script setup>
import { IonMenuToggle, menuController } from "@ionic/vue"
import { FeatherIcon } from "frappe-ui"

import { computed, ref } from "vue"
import { useRoute, useRouter } from "vue-router"

const menuItems = ref([
	{
		icon: "home",
		title: "Home",
		route: {
			name: "Home",
		},
		current: false,
	},
	{
		icon: "calendar",
		title: "Leaves & Holidays",
		route: {
			name: "Leaves",
		},
		current: false,
	},
	{
		icon: "dollar-sign",
		title: "Expense Claims",
		route: {
			name: "ExpenseClaims",
		},
		current: false,
	},
	{
		icon: "check-circle",
		title: "Attendance",
		route: {
			name: "Login",
		},
		current: false,
	},
	{
		icon: "file",
		title: "Salary Slips",
		route: {
			name: "SalarySlips",
		},
	},
	{
		icon: "file",
		title: "Test1",
		route: {
			name: "Test1",
		},
	},
	{
		icon: "file",
		title: "Test2",
		route: {
			name: "Test2",
		},
	}
])

const route = useRoute()
const router = useRouter()

const currentRoute = computed(() => {
	menuItems.value.forEach((item) => {
		item.current = item.route.name === route.name
	})
	return route.name
})

const navigate = async (route) => {
	await menuController.close()
	if (route.name === currentRoute.value) {
		return
	}
	router.push(route)
}
</script>
