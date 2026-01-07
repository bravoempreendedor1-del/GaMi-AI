# Logo GaMi-AI

Para adicionar a logo ao sistema:

1. **Salve a imagem da logo** com o nome `logo.png` na pasta `public/`
   - Formatos suportados: PNG, SVG, JPG
   - Tamanho recomendado: 200x60px (ou proporcional)

2. **O sistema já está configurado** para usar:
   - Logo: `/public/logo.png`
   - Favicon: `/public/logo.png`

3. **Se usar outro nome ou formato**, edite o arquivo `.chainlit/config.toml`:
   ```toml
   logo = "/public/seu-arquivo.png"
   favicon = "/public/seu-arquivo.png"
   ```

A logo aparecerá:
- No cabeçalho superior da aplicação
- Na aba do navegador (favicon)
- Com fundo preto e borda ciano para destacar

