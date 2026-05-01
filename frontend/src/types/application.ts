export interface TenantInfo {
  name: string
  residentNumber: string  // 전송 시만 사용
  address: string
  addressDetail?: string  // 동, 호수
  phone: string
}

export interface LandlordInfo {
  name: string
  address: string
  addressDetail?: string  // 동, 호수
  phone: string
  corpNumber?: string
  isCorporate: boolean
}

export interface PropertyInfo {
  address: string
  addressDetail?: string  // 동, 호수
}

export interface ContractInfo {
  contractDate: string    // ISO 날짜
  depositAmount: number   // 원 단위
  confirmedDate?: string
  moveInDate?: string
}

export interface ApplicationFormData {
  tenant: TenantInfo
  landlord: LandlordInfo
  property: PropertyInfo
  contract: ContractInfo
}

export type ApplicationStatus =
  | 'pending'
  | 'collecting'
  | 'analyzing'
  | 'ready'
  | 'filling'
  | 'preview'
  | 'submitted'
  | 'failed'

export interface ProgressUpdate {
  applicationId: string
  status: ApplicationStatus
  progress: number      // 0 ~ 100
  currentStep: string
  completedDocs: string[]
  failedDocs: string[]
  message: string
}

export interface FeeBreakdown {
  stampDuty: number         // 인지대 1,800원
  deliveryFee: number       // 송달료 31,200원
  registrationTax: number   // 등록면허세 7,200원
  registryCommission: number // 등기촉탁수수료 3,000원
  total: number             // 합계 43,200원
}

export const DOCUMENT_LABELS: Record<string, string> = {
  building_registry: '건물등기사항증명서',
  resident_registration: '주민등록초본',
  lease_contract: '임대차계약서',
  termination_notice: '계약해지통지서',
  corporate_registry: '법인등기사항증명서',
  building_ledger: '건축물대장',
  floor_plan: '별지 도면',
}
