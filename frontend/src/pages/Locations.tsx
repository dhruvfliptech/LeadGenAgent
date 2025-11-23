import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { PlusIcon, PencilIcon, TrashIcon } from '@heroicons/react/24/outline'
import toast from 'react-hot-toast'
import { api } from '@/services/api'
import { Location } from '@/types/location'

export default function Locations() {
  const [isAddingLocation, setIsAddingLocation] = useState(false)
  const [editingLocation, setEditingLocation] = useState<Location | null>(null)
  const queryClient = useQueryClient()

  const { data: locations, isLoading } = useQuery<Location[]>({
    queryKey: ['locations'],
    queryFn: () => api.get('/locations').then(res => res.data),
  })

  const createLocationMutation = useMutation({
    mutationFn: (data: Partial<Location>) => api.post('/locations', data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      setIsAddingLocation(false)
      toast.success('Location created successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to create location')
    },
  })

  const updateLocationMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<Location> }) =>
      api.put(`/locations/${id}`, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      setEditingLocation(null)
      toast.success('Location updated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to update location')
    },
  })

  const deleteLocationMutation = useMutation({
    mutationFn: (id: number) => api.delete(`/locations/${id}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['locations'] })
      toast.success('Location deactivated successfully')
    },
    onError: (error: any) => {
      toast.error(error.response?.data?.detail || 'Failed to deactivate location')
    },
  })

  const handleSubmit = (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const formData = new FormData(e.currentTarget)
    const data = {
      name: formData.get('name') as string,
      code: formData.get('code') as string,
      url: formData.get('url') as string,
      state: formData.get('state') as string,
      country: formData.get('country') as string || 'US',
      is_active: true,
    }

    if (editingLocation) {
      updateLocationMutation.mutate({ id: editingLocation.id, data })
    } else {
      createLocationMutation.mutate(data)
    }
  }

  if (isLoading) {
    return (
      <div className="space-y-6">
        <div className="h-8 bg-gray-200 rounded animate-pulse"></div>
        <div className="card p-6 space-y-4">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="h-16 bg-gray-200 rounded animate-pulse"></div>
          ))}
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="flex-1 min-w-0">
          <h2 className="text-2xl font-bold leading-7 text-gray-900 sm:text-3xl sm:truncate">
            Locations
          </h2>
          <p className="mt-1 text-sm text-gray-500">
            Manage Craigslist locations for scraping
          </p>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <button
            onClick={() => setIsAddingLocation(true)}
            className="btn-primary"
          >
            <PlusIcon className="w-4 h-4 mr-2" />
            Add Location
          </button>
        </div>
      </div>

      {/* Add/Edit Form */}
      {(isAddingLocation || editingLocation) && (
        <div className="card p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">
            {editingLocation ? 'Edit Location' : 'Add New Location'}
          </h3>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="form-label">Location Name</label>
                <input
                  type="text"
                  name="name"
                  required
                  defaultValue={editingLocation?.name}
                  placeholder="e.g., San Francisco Bay Area"
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Location Code</label>
                <input
                  type="text"
                  name="code"
                  required
                  defaultValue={editingLocation?.code}
                  placeholder="e.g., sfbay"
                  className="form-input"
                />
              </div>
              <div className="md:col-span-2">
                <label className="form-label">Craigslist URL</label>
                <input
                  type="url"
                  name="url"
                  required
                  defaultValue={editingLocation?.url}
                  placeholder="https://sfbay.craigslist.org"
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">State/Province</label>
                <input
                  type="text"
                  name="state"
                  defaultValue={editingLocation?.state}
                  placeholder="e.g., California"
                  className="form-input"
                />
              </div>
              <div>
                <label className="form-label">Country</label>
                <input
                  type="text"
                  name="country"
                  defaultValue={editingLocation?.country || 'US'}
                  className="form-input"
                />
              </div>
            </div>
            <div className="flex justify-end space-x-3">
              <button
                type="button"
                onClick={() => {
                  setIsAddingLocation(false)
                  setEditingLocation(null)
                }}
                className="btn-secondary"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={createLocationMutation.isPending || updateLocationMutation.isPending}
                className="btn-primary"
              >
                {createLocationMutation.isPending || updateLocationMutation.isPending
                  ? 'Saving...'
                  : editingLocation
                  ? 'Update Location'
                  : 'Add Location'}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Locations List */}
      {locations && locations.length > 0 ? (
        <div className="card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Code
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    URL
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {locations.map((location) => (
                  <tr key={location.id} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="flex flex-col">
                        <div className="text-sm font-medium text-gray-900">
                          {location.name}
                        </div>
                        {location.state && (
                          <div className="text-sm text-gray-500">
                            {location.state}, {location.country}
                          </div>
                        )}
                      </div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <code className="text-sm bg-gray-100 px-2 py-1 rounded">
                        {location.code}
                      </code>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <a
                        href={location.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary-600 hover:text-primary-900 truncate max-w-xs block"
                      >
                        {location.url}
                      </a>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span
                        className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                          location.is_active
                            ? 'bg-green-100 text-green-800'
                            : 'bg-red-100 text-red-800'
                        }`}
                      >
                        {location.is_active ? 'Active' : 'Inactive'}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <div className="flex items-center justify-end space-x-2">
                        <button
                          onClick={() => setEditingLocation(location)}
                          className="text-primary-600 hover:text-primary-900"
                        >
                          <PencilIcon className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => {
                            if (confirm('Are you sure you want to deactivate this location?')) {
                              deleteLocationMutation.mutate(location.id)
                            }
                          }}
                          className="text-red-600 hover:text-red-900"
                          disabled={deleteLocationMutation.isPending}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        <div className="card">
          <div className="text-center py-12">
            <div className="text-gray-500 mb-4">No locations configured yet.</div>
            <button
              onClick={() => setIsAddingLocation(true)}
              className="btn-primary"
            >
              Add Your First Location
            </button>
          </div>
        </div>
      )}
    </div>
  )
}