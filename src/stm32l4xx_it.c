#include "main.h"
#include "stm32l4xx_it.h"

void SysTick_Handler(void)
{
  HAL_IncTick();
}
