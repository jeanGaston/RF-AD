# Server install

## 1. Modify the LDAP Schema

To add the `rFIDUID` attribute to your LDAP schema, follow these steps:

### Open PowerShell as Administrator

1. **Open PowerShell as Administrator**: This is required to make changes to the LDAP schema.

### Add the `rFIDUID` Attribute

2. **Add the `rFIDUID` Attribute**: Use the following PowerShell commands to add the `rFIDUID` attribute to the LDAP schema.

   ```powershell
   Import-Module ActiveDirectory

   # Define the new attribute
   $attribute = New-Object PSObject -Property @{
       lDAPDisplayName = "rFIDUID"
       adminDescription = "RFID UID"
       attributeSyntax = "2.5.5.12"
       oMSyntax = 64
       isSingleValued = $true
   }

   # Add the new attribute to the schema
   New-ADObject -Name "rFIDUID" -Type "attributeSchema" -OtherAttributes $attribute

3. **Add the Attribute to a Class**: Update the user class to include the `rFIDUID` attribute.
    ```powershell
    # Find the user class
    $userClass = Get-ADObject -LDAPFilter "(cn=user)" -SearchBase "CN=Schema,CN=Configuration,DC=ad,DC=bts,DC=com" -SearchScope Base

    # Add the new attribute to the user class
    Set-ADObject -Identity $userClass -Add @{mayContain="rFIDUID"}
    ```

## 2. Create an LDAP User for Sync
Create a dedicated LDAP user for synchronizing data:  
⚠️ Do not forget to replace the domain by yours and the password by a strong one.
```powershell
    New-ADUser -Name "RO.RF-AD" `
        -GivenName "ReadOnly" `
        -Surname "AD" `
        -UserPrincipalName "RO.RF-AD@your-domain.com" `
        -Path "OU=Users,DC=your-domain,DC=com" `
        -AccountPassword (ConvertTo-SecureString -AsPlainText "[YOUR PASSWORD]" -Force) `
        -Enabled $true

    # Grant read permissions
    $ldapUser = Get-ADUser -Identity "RO.RF-AD"
    Add-ADPermission -Identity "OU=Users,DC=your-domain,DC=com" -User $ldapUser -AccessRights ReadProperty
    ```

