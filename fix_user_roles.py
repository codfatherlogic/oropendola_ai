import frappe

frappe.connect()
frappe.set_user('Administrator')

user = 'sammish@oropendola.ai'

# Check current roles
roles = frappe.get_roles(user)
print(f"Current roles for {user}: {roles}")

# Remove desk roles if they exist
desk_roles = ['Desk User', 'System Manager', 'Sales User', 'Stock User']
user_doc = frappe.get_doc('User', user)

print(f"\nRoles in User doc:")
for role in user_doc.roles:
    print(f"  - {role.role}")

# Keep only essential website roles
should_remove = []
for role in user_doc.roles:
    if role.role in desk_roles:
        should_remove.append(role)
        print(f"\nRemoving desk role: {role.role}")

for role in should_remove:
    user_doc.remove(role)

# Ensure they have Website User role
has_website_user = any(r.role == 'Website User' for r in user_doc.roles)
if not has_website_user:
    user_doc.append('roles', {'role': 'Website User'})
    print("\nAdded Website User role")

user_doc.save()
frappe.db.commit()

print(f"\nFinal roles: {frappe.get_roles(user)}")
print("\nUser roles updated successfully!")
