const { chromium } = require('playwright');
const fs = require('fs');

const outDir = '/home/claude/divibond/screenshots';
fs.mkdirSync(outDir, { recursive: true });

(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 390, height: 760 } });

  await page.goto('http://127.0.0.1:8080/index.html');
  await page.waitForSelector('.metric-grid');
  await page.screenshot({ path: `${outDir}/01_home_bonds.png` });

  // Главная: переключение на вкладку "Акции"
  await page.click('.segmented button:has-text("Акции")');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${outDir}/02_home_stocks.png` });

  // Список облигаций
  await page.click('.nav-item:has-text("Облигации")');
  await page.waitForSelector('.filter-btn');
  await page.screenshot({ path: `${outDir}/03_bonds_list.png` });

  // Карточка облигации с переменным купоном — должно быть предупреждение
  await page.click('.card:has-text("ВТБ Б1-99")');
  await page.waitForSelector('.warning');
  await page.screenshot({ path: `${outDir}/04_bond_detail_floating.png` });

  // Добавляем в избранное (звезда в шапке) и возвращаемся к списку
  await page.locator('#app-header .icon-btn').last().click();
  await page.locator('#app-header .icon-btn').first().click();
  await page.waitForSelector('.filter-btn');

  // Экран фильтров: доходность от 10%, срок "более 5 лет"
  await page.click('.filter-btn');
  await page.waitForSelector('#filter-sheet-content .filter-input');
  await page.locator('#filter-sheet-content .filter-input').nth(0).fill('10');
  await page.click('#filter-sheet-content .chip:has-text("Более 5 лет")');
  await page.screenshot({ path: `${outDir}/05_bonds_filters.png` });

  await page.click('#filter-sheet-content button:has-text("Показать")');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${outDir}/06_bonds_filtered.png` });

  // Список акций -> карточка SBER с историей дивидендов
  await page.click('.nav-item:has-text("Акции")');
  await page.waitForSelector('.filter-btn');
  await page.click('.card:has-text("SBER")');
  await page.waitForSelector('.warning');
  await page.screenshot({ path: `${outDir}/07_stock_detail.png` });
  await page.locator('#app-header .icon-btn').last().click(); // в избранное

  // Избранное: должны быть и облигация, и акция, с возможностью удаления
  await page.click('.nav-item:has-text("Избранное")');
  await page.waitForTimeout(300);
  await page.screenshot({ path: `${outDir}/08_favorites.png` });

  await browser.close();
  console.log('Скриншоты сохранены в', outDir);
})();
