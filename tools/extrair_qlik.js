// Runs on the MAPA panel page (mapa-indicadores.agricultura.gov.br/publico/extensions/Fertilizantes/Fertilizantes.html).
// Extracts SIPEAGRO products (with guarantees) and establishment contacts through the page's own Qlik API.
(async () => {
  const APP = '76ef621a-8dc4-48de-8fe0-0aa7e5a47181';
  for (let i = 0; i < 60 && typeof window.require !== 'function'; i++) await new Promise(r => setTimeout(r, 500));
  const qlik = await new Promise(r => require(['js/qlik'], r));
  const app = qlik.openApp(APP, { host: location.hostname, prefix: '/publico/', port: location.port, isSecure: location.protocol === 'https:' });
  const P = 'FERTILIZANTE_PROD_SIPE_', E = 'FERTILIZANTE_ESTAB_SIPE_';
  const cat = (f, sep) => `Concat(DISTINCT [${f}], '${sep || ' / '}')`;
  async function table(dim, measures) {
    const model = await app.createCube({
      qDimensions: [{ qDef: { qFieldDefs: [dim] } }],
      qMeasures: measures.map(m => ({ qDef: { qDef: m } })),
      qInitialDataFetch: [{ qTop: 0, qLeft: 0, qHeight: 0, qWidth: 0 }]
    });
    const layout = await model.getLayout();
    const total = layout.qHyperCube.qSize.qcy, w = measures.length + 1, h = Math.floor(10000 / w);
    const rows = [];
    for (let top = 0; top < total; top += h) {
      const pages = await model.getHyperCubeData('/qHyperCubeDef', [{ qTop: top, qLeft: 0, qWidth: w, qHeight: h }]);
      pages[0].qMatrix.forEach(r => rows.push(r.map(c => (c.qText === '-' ? '' : c.qText))));
    }
    app.destroySessionObject(layout.qInfo.qId);
    return rows;
  }
  const produtos = await table(P + 'NUM_PRODUTO', [
    `Only([${P}CD_REGISTRO_ESTABELECIMENTO])`,
    cat(P + 'NM_PRODUTO_SIPE'),
    cat(P + 'DS_CLASSIFICACA'),
    cat(P + 'DS_TIPO_FERTILIZANTE'),
    cat(P + 'SITUACAO_REGISTRO'),
    `Date(Max([${P}DT_CONCESSAO_REGISTRO]), 'DD/MM/YYYY')`,
    cat(P + 'NATUREZA_FISICA'),
    `Concat(DISTINCT [${P}DS_GARANTIA] & '|' & [${P}VL_GARANTIA_COMPONENTE_PROD] & '|' & [${P}SG_UNIDADE_MEDIDA_SIPE], '¦')`,
    cat(P + 'DS_CARACTERISTICA_ADICIONAL'),
    cat(P + 'MODO_APLICACAO')
  ]);
  const contatos = await table(E + 'CD_REGISTRO_ESTABELECIMENTO', [
    `Concat(DISTINCT [${E}NR_TELEFONE], ' / ')`,
    `Concat(DISTINCT If([${E}ED_EMAIL] <> '-', Lower([${E}ED_EMAIL])), ' / ')`,
    `Only([${E}ENDERECO_SIPEAGRO])`
  ]);
  return JSON.stringify({ produtos, contatos, extraido: new Date().toISOString() });
})()
