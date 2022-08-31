# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors and contributors
# For license information, please see license.txt

import datetime

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.model.mapper import get_mapped_doc
from frappe.utils import cint, flt, get_link_to_form, getdate


class JobOffer(Document):
	def onload(self):
		employee = frappe.db.get_value("Employee", {"job_applicant": self.job_applicant}, "name") or ""
		self.set_onload("employee", employee)

	def validate(self):
		self.validate_vacancies()
		job_offer = frappe.db.exists(
			"Job Offer", {"job_applicant": self.job_applicant, "docstatus": ["!=", 2]}
		)
		if job_offer and job_offer != self.name:
			frappe.throw(
				_("Job Offer: {0} is already for Job Applicant: {1}").format(
					frappe.bold(job_offer), frappe.bold(self.job_applicant)
				)
			)

	def validate_vacancies(self):
		staffing_plan = get_staffing_plan_detail(self.designation, self.company, self.offer_date)
		check_vacancies = frappe.get_single("HR Settings").check_vacancies
		if staffing_plan and check_vacancies:
			job_offers = self.get_job_offer(staffing_plan.from_date, staffing_plan.to_date)
			if not staffing_plan.get("vacancies") or cint(staffing_plan.vacancies) - len(job_offers) <= 0:
				error_variable = "for " + frappe.bold(self.designation)
				if staffing_plan.get("parent"):
					error_variable = frappe.bold(get_link_to_form("Staffing Plan", staffing_plan.parent))

				frappe.throw(_("There are no vacancies under staffing plan {0}").format(error_variable))

	def on_change(self):
		update_job_applicant(self.status, self.job_applicant)

	def get_job_offer(self, from_date, to_date):
		"""Returns job offer created during a time period"""
		return frappe.get_all(
			"Job Offer",
			filters={
				"offer_date": ["between", (from_date, to_date)],
				"designation": self.designation,
				"company": self.company,
				"docstatus": 1,
			},
			fields=["name"],
		)

	@frappe.whitelist()
	def pull_salary_structure(self):
		self.salary_breakup = []
		salary_structure = frappe.get_doc("Salary Structure", self.salary_structure)
		data, default_data = self.get_data_for_eval(salary_structure)

		gross = 0
		for struct_row in salary_structure.get("earnings"):
			amount = self.eval_condition_and_formula(struct_row, data)
			if amount and struct_row.statistical_component == 0:
				self.append(
					"salary_breakup",
					{
						"salary_component": struct_row.salary_component,
						"monthly_amount": amount,
						"yearly_amount": amount * 12,
						"group": "Fixed Components",
					},
				)
				gross += amount

		# add gross
		self.append(
			"salary_breakup",
			{
				"salary_component": "Gross",
				"monthly_amount": round(gross),
				"yearly_amount": round(gross * 12),
			},
		)

		pf = 0
		for struct_row in salary_structure.get("deductions"):
			if struct_row.salary_component == "Provident Fund":
				amount = self.eval_condition_and_formula(struct_row, data)
				if amount and struct_row.statistical_component == 0:
					self.append(
						"salary_breakup",
						{
							"salary_component": struct_row.salary_component,
							"monthly_amount": amount,
							"yearly_amount": amount * 12,
							"group": "Statutory Components",
						},
					)
					pf = amount

		self.append(
			"salary_breakup",
			{
				"salary_component": "CTC",
				"monthly_amount": round(gross + pf),
				"yearly_amount": round((gross + pf) * 12),
			},
		)

		self.append(
			"salary_breakup",
			{
				"salary_component": "Take home*",
				"monthly_amount": round(gross - pf),
				"yearly_amount": round((gross - pf) * 12),
			},
		)

		return self

	def eval_condition_and_formula(self, d, data):
		whitelisted_globals = {
			"int": int,
			"float": float,
			"long": int,
			"round": round,
			"date": datetime.date,
			"getdate": getdate,
		}

		try:
			condition = d.condition.strip().replace("\n", " ") if d.condition else None
			if condition:
				if not frappe.safe_eval(condition, whitelisted_globals, data):
					return None
			amount = d.amount
			if d.amount_based_on_formula:
				formula = d.formula.strip().replace("\n", " ") if d.formula else None
				if formula:
					amount = flt(frappe.safe_eval(formula, whitelisted_globals, data), d.precision("amount"))
			if amount:
				data[d.abbr] = amount

			return amount

		except NameError as err:
			frappe.throw(
				_("{0} <br> This error can be due to missing or deleted field.").format(err),
				title=_("Name error"),
			)
		except SyntaxError as err:
			frappe.throw(_("Syntax error in formula or condition: {0}").format(err))
		except Exception as e:
			frappe.throw(_("Error in formula or condition: {0}").format(e))
			raise

	def get_data_for_eval(self, salary_structure):
		"""Returns data for evaluating formula"""
		data = frappe._dict()
		# employee = frappe.get_doc("Employee", self.employee).as_dict()

		data.update({"base": self.base, "variable": self.variable})
		# data.update(employee)
		data.update(self.as_dict())

		# set values for components
		salary_components = frappe.get_all("Salary Component", fields=["salary_component_abbr"])
		for sc in salary_components:
			data.setdefault(sc.salary_component_abbr, 0)

		# shallow copy of data to store default amounts (without payment days) for tax calculation
		default_data = data.copy()

		for key in ("earnings", "deductions"):
			for d in salary_structure.get(key):
				default_data[d.abbr] = d.default_amount
				data[d.abbr] = d.amount

		return data, default_data


def update_job_applicant(status, job_applicant):
	if status in ("Accepted", "Rejected"):
		frappe.set_value("Job Applicant", job_applicant, "status", status)


def get_staffing_plan_detail(designation, company, offer_date):
	detail = frappe.db.sql(
		"""
		SELECT DISTINCT spd.parent,
			sp.from_date as from_date,
			sp.to_date as to_date,
			sp.name,
			sum(spd.vacancies) as vacancies,
			spd.designation
		FROM `tabStaffing Plan Detail` spd, `tabStaffing Plan` sp
		WHERE
			sp.docstatus=1
			AND spd.designation=%s
			AND sp.company=%s
			AND spd.parent = sp.name
			AND %s between sp.from_date and sp.to_date
	""",
		(designation, company, offer_date),
		as_dict=1,
	)

	return frappe._dict(detail[0]) if (detail and detail[0].parent) else None


@frappe.whitelist()
def make_employee(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.personal_email, target.first_name = frappe.db.get_value(
			"Job Applicant", source.job_applicant, ["email_id", "applicant_name"]
		)

	doc = get_mapped_doc(
		"Job Offer",
		source_name,
		{
			"Job Offer": {
				"doctype": "Employee",
				"field_map": {"applicant_name": "employee_name", "offer_date": "scheduled_confirmation_date"},
			}
		},
		target_doc,
		set_missing_values,
	)
	return doc


@frappe.whitelist()
def get_offer_acceptance_rate(company=None, department=None):
	filters = {"docstatus": 1}
	if company:
		filters["company"] = company
	if department:
		filters["department"] = department

	total_offers = frappe.db.count("Job Offer", filters=filters)

	filters["status"] = "Accepted"
	total_accepted = frappe.db.count("Job Offer", filters=filters)

	return {
		"value": flt(total_accepted) / flt(total_offers) * 100 if total_offers else 0,
		"fieldtype": "Percent",
	}
