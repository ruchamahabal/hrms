import { createApp } from "vue"
import App from "./App.vue"
import router from "./router"
import socket from "./socket"

import {
	Button,
	Input,
	setConfig,
	frappeRequest,
	resourcesPlugin,
	FormControl,
} from "frappe-ui"
import EmptyState from "@/components/EmptyState.vue"

import { IonicVue } from "@ionic/vue"

import { session } from "@/data/session"
import { userResource } from "@/data/user"
import { employeeResource } from "@/data/employee"
import { menu } from "@/data/menu"

import dayjs from "@/utils/dayjs"
// import getIonicConfig from "@/utils/ionicConfig"

/* Core CSS required for Ionic components to work properly */
import "@ionic/vue/css/core.css"

/* Theme variables */
import "./theme/variables.css"

import "./main.css"

import { isPlatform, menuController } from "@ionic/vue"
import { createAnimation, iosTransitionAnimation } from "@ionic/core"
/**
 * on iOS, the back swipe gesture triggers the animation twice:
 * the safari's default back swipe animation & ionic's animation
 * The config here takes care of the same
 */

export const animationBuilder = (baseEl, opts) => {
	if (opts.direction === "back") {
		/**
		 * Even after disabling swipeBackEnabled, when the swipe is completed & we're back on the first screen
		 * the "pop" animation is triggered, resulting in a double animation
		 * HACK: return empty animation for back swipe in ios
		 **/
		return createAnimation()
	}

	return iosTransitionAnimation(baseEl, opts)
}

const getIonicConfig = () => {
	return isPlatform("iphone")
		? {
				// disable ionic's swipe back gesture on ios
				swipeBackEnabled: false,
				navAnimation: animationBuilder,
		  }
		: {}
}

const app = createApp(App)

setConfig("resourceFetcher", frappeRequest)
app.use(resourcesPlugin)

app.component("Button", Button)
app.component("Input", Input)
app.component("FormControl", FormControl)
app.component("EmptyState", EmptyState)

app.use(router)
app.use(IonicVue, getIonicConfig())

if (session?.isLoggedIn && !employeeResource?.data) {
	employeeResource.reload()
}

app.provide("$session", session)
app.provide("$user", userResource)
app.provide("$employee", employeeResource)
app.provide("$socket", socket)
app.provide("$dayjs", dayjs)

router.isReady().then(() => {
	app.mount("#app")
})

router.beforeEach(async (to, from, next) => {
	// let isLoggedIn = session.isLoggedIn
	// try {
	// 	await userResource.promise
	// } catch (error) {
	// 	isLoggedIn = false
	// }

	// if (isLoggedIn) {
	// 	await employeeResource.promise
	// }

	// if (to.name === "Login" && isLoggedIn) {
	// 	next({ name: "Home" })
	// } else if (to.name !== "Login" && !isLoggedIn) {
	// 	next({ name: "Login" })
	// } else {
	// 	next()
	// }
	menuController.close("main-menu")
	next()
})
