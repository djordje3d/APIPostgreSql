import { api } from './client'

export interface UploadTicketImageResponse {
  url: string
}

/**
 * Upload a ticket image (JPEG, PNG, WebP). Client should resize before calling.
 * Returns the URL path to pass as image_url when creating the ticket.
 */
export function uploadTicketImage(file: File | Blob, filename?: string): Promise<UploadTicketImageResponse> {
  const formData = new FormData()
  const name = filename ?? (file instanceof File ? file.name : 'image.jpg')
  formData.append('file', file, name) // add the file to the form data
  return api
    .post<UploadTicketImageResponse>('/upload/ticket-image', formData, { // post the form data to the upload/ticket-image endpoint
      headers: {
        'Content-Type': undefined as unknown as string,
      },
      timeout: 15000,
    })
    .then((res) => res.data) // return the data from the response
}
