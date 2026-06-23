#include "stm32l4xx.h"

#if !defined  (HSE_VALUE)
#define HSE_VALUE    8000000U
#endif

#if !defined  (MSI_VALUE)
#define MSI_VALUE    4000000U
#endif

uint32_t SystemCoreClock = 4000000U;
const uint8_t AHBPrescTable[16] = {0U, 0U, 0U, 0U, 0U, 0U, 0U, 0U, 1U, 2U, 3U, 4U, 6U, 7U, 8U, 9U};
const uint8_t APBPrescTable[8] = {0U, 0U, 0U, 0U, 1U, 2U, 3U, 4U};
const uint32_t MSIRangeTable[12] = {
  100000U, 200000U, 400000U, 800000U, 1000000U, 2000000U,
  4000000U, 8000000U, 16000000U, 24000000U, 32000000U, 48000000U
};

void SystemInit(void)
{
#if defined (__FPU_PRESENT) && (__FPU_PRESENT == 1U) && defined (__FPU_USED) && (__FPU_USED == 1U)
  SCB->CPACR |= ((3UL << 20U) | (3UL << 22U));
#endif

  RCC->CR |= RCC_CR_MSION;
  RCC->CFGR = 0x00000000U;
  RCC->CR &= ~(RCC_CR_HSION | RCC_CR_HSEON | RCC_CR_PLLON | RCC_CR_HSI48ON);
  RCC->PLLCFGR = 0x00001000U;
  RCC->CR &= ~(RCC_CR_HSEBYP);
  RCC->CIER = 0x00000000U;
}

void SystemCoreClockUpdate(void)
{
  uint32_t msirange;
  uint32_t pllvco;
  uint32_t pllr;
  uint32_t pllsource;
  uint32_t sysclk_source;

  sysclk_source = RCC->CFGR & RCC_CFGR_SWS;
  switch (sysclk_source)
  {
    case RCC_CFGR_SWS_HSI:
      SystemCoreClock = HSI_VALUE;
      break;
    case RCC_CFGR_SWS_HSE:
      SystemCoreClock = HSE_VALUE;
      break;
    case RCC_CFGR_SWS_PLL:
      pllsource = RCC->PLLCFGR & RCC_PLLCFGR_PLLSRC;
      if (pllsource == RCC_PLLCFGR_PLLSRC_HSE)
      {
        pllvco = HSE_VALUE;
      }
      else if (pllsource == RCC_PLLCFGR_PLLSRC_HSI)
      {
        pllvco = HSI_VALUE;
      }
      else
      {
        msirange = (RCC->CR & RCC_CR_MSIRANGE) >> RCC_CR_MSIRANGE_Pos;
        pllvco = MSIRangeTable[msirange];
      }
      pllvco = (pllvco / (((RCC->PLLCFGR & RCC_PLLCFGR_PLLM) >> RCC_PLLCFGR_PLLM_Pos) + 1U)) *
               ((RCC->PLLCFGR & RCC_PLLCFGR_PLLN) >> RCC_PLLCFGR_PLLN_Pos);
      pllr = (((RCC->PLLCFGR & RCC_PLLCFGR_PLLR) >> RCC_PLLCFGR_PLLR_Pos) + 1U) * 2U;
      SystemCoreClock = pllvco / pllr;
      break;
    case RCC_CFGR_SWS_MSI:
    default:
      msirange = (RCC->CR & RCC_CR_MSIRANGE) >> RCC_CR_MSIRANGE_Pos;
      SystemCoreClock = MSIRangeTable[msirange];
      break;
  }

  SystemCoreClock >>= AHBPrescTable[((RCC->CFGR & RCC_CFGR_HPRE) >> RCC_CFGR_HPRE_Pos)];
}
