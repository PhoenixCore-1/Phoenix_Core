import { api } from "../../../core/api/client"

export async function uploadCustomerMaster(file: File) {
  const formData = new FormData()
  formData.append("file", file)

  return api<{
    id: string
    status: string
  }>("/api/v1/company/imports/customer-master", {
    method: "POST",
    body: formData,
  })
}