import router from "@/router"
import { computed } from "vue"
import { createResource } from "frappe-ui"

export const employeeResource = createResource({
	url: "hrms.api.get_current_employee_info",
	cache: "Employee",
	onError(error) {
		if (error && error.exc_type === "AuthenticationError") {
			router.push("/login")
		}
	},
})

export function getEmployee() {
	return employeeResource.data
}

export const employee = computed(() => employeeResource.data)