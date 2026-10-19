# Technical Note: ITLingoCloud Parser Adaptations for RSL and ASL Specifications

**To:** Prof. Alberto Rodrigues da Silva  
**From:** Denilson Fragoso Da Silva Santos (IST-1113142)  
**Subject:** Parser constraints and adaptations in RSL v3.2 and ASL v3.3  

Dear Professor Alberto,

Following your feedback to provide more detailed specifications, I have developed **RSL v3.2** and **ASL v3.3** for the AI Project Management Ecosystem. Both specifications have been validated with **zero syntax errors** in the ITLingoCloud platform. 

To achieve this, certain structural adaptations were required due to the strict validation rules of the ITLingoCloud parser. I am documenting these changes below to clarify that they are tool-related constraints and do not represent architectural compromises to the ecosystem.

### 1. RSL v3.2 Adaptations
- **Stakeholders (`isExternal` attribute):** The parser does not accept the `isExternal` attribute for Stakeholders. This semantic information was moved to the `description` field, and the external nature is already implicitly captured by the types `Organization_Customer` and `System_External`.
- **Stakeholders (Concerns/Responsibilities):** The `concern` and `responsibility` attributes are not supported by the current parser version for Stakeholders. All this information has been consolidated textually into the `description` field.
- **Quality Requirements (QR subtypes):** The parser restricts QR subtypes to standard ones. The `: TimeBehavior` subtype was removed, and the related metrics (e.g., 15s, 99%) are explicitly stated in the `description` text of the `: Performance` or `: Reliability` QRs.

### 2. ASL v3.3 Adaptations
- **Permissions (`resource` binding):** The `resource` declaration inside `SecPermission` must be placed inside the body block (e.g., `[ resource e_User ]`), rather than inline. 
- **Views (`DataEntityView`):** The parser's valid View type set does not include `DataEntityView`. The specification was updated to use `: DataView`.
- **Component Wiring (`on X.Y.Z do action`):** The parser only resolves component paths in action wirings if the components are declared *inline* within the page container. Therefore, components like `messageInput` and `projectForm` were moved inline to allow the explicit wiring of their events to system actions.
- **Default Route:** `defaultRoute` must point to a valid, declared route (`rAssistantChat`).

These adaptations ensure the specifications are syntactically valid and machine-readable by the ITLingoCloud parser, while preserving the semantic richness of the system's architecture.

The updated files are available in the repository (`docs/specs/RSL_v3.2.rsl` and `docs/specs/ASL_v3.3.asl`).

Best regards,  
Denilson Fragoso Da Silva Santos
