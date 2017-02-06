import React from 'react';
import { Button, Table } from 'react-bootstrap';

export const Treds = require('../../api/documents/treds.json');

const inheritanceFullNames = {
  AD: 'Autosomal dominant',
  AR: 'Autosomal recessive',
  XLD: 'X-linked dominant',
  XLR: 'X-linked recessive',
};

const TredTable = React.createClass({
  propTypes: {
    name: React.PropTypes.string,
  },

  render() {
    const name = this.props.name;

    if (!name) {
      return null;
    }

    const tred = Treds[name];
    //console.log(tred);
    [start, end] = tred["repeat_location"].split(':')[1].split('-')
    const repeatcounts = (end - start + 1) / tred["repeat"].length;

    return (
      <Table striped condensed hover>
        <tbody>
          <tr>
            <td>Gene</td>
            <td>
              <a href={ `https://www.genecards.org/cgi-bin/carddisp.pl?gene=${tred.gene_name}` }
                title={ tred.gene_name }
                target='_blank'
              >
                { tred.gene_name }
              </a> ({ tred.gene_location } on hg38) - { tred.gene_part }
            </td>
          </tr>
          <tr>
            <td>Inheritance</td>
            <td>{ inheritanceFullNames[tred.inheritance] }</td>
          </tr>
          <tr>
            <td>Sequence</td>
            <td>
              { tred.prefix }
              <div style={{ color: 'red' }}>
                <strong>({ tred.repeat })x</strong>
              </div>
              { tred.suffix }
              <div style={{ color: 'grey' }}>
                x={ repeatcounts } in hg38
              </div>
            </td>
          </tr>
          <tr>
            <td>Symptom</td>
            <td>
              <div className="text-left">
                { tred.symptom }
              </div>
              <div>
                { tred.omim_id ? <Button bsStyle='link'
                  href={ `http://www.omim.org/entry/${tred.omim_id}` }>OMIM</Button> : null }
                { tred.src != 'omim' ? <Button bsStyle='link'
                  href={ tred.url }>{ tred.src }</Button> : null}
              </div>
            </td>
          </tr>
        </tbody>
      </Table>
    );
  },
});

module.exports = TredTable;
