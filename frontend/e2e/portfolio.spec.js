import {test,expect} from '@playwright/test';
test('navegar al recorrido laboral',async({page})=>{
 await page.goto('/'); await page.getByRole('link',{name:'Conoce mi recorrido'}).click();
 await expect(page).toHaveURL(/#experiencia$/); await expect(page.getByRole('heading',{name:'Mi experiencia laboral'})).toBeVisible();
});
test('mostrar idiomas sin datos inventados',async({page})=>{
 await page.goto('/'); await page.getByRole('link',{name:'Idiomas',exact:true}).click();
 await expect(page.getByText('Palabras que abren puertas')).toBeVisible();
});
test('enviar contacto a la API real',async({page})=>{
 await page.goto('/'); await page.getByLabel('Tu nombre').fill('Prueba E2E');
 await page.getByLabel('Correo electrónico').fill('e2e@example.com');
 await page.getByLabel('Tu mensaje').fill('Este es un mensaje de prueba automatizada.');
 await page.getByRole('button',{name:'Enviar mensaje'}).click();
 await expect(page.getByRole('status')).toContainText('Tu mensaje quedó guardado');
});
