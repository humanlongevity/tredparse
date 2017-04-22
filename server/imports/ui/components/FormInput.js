import React from 'react';
import { ButtonGroup, ButtonToolbar, Button, FormControl, Form, FormGroup, HelpBlock, Panel } from 'react-bootstrap';
import { Typeahead } from 'react-bootstrap-typeahead';
import Settings from './Settings';
import { Treds } from './TredTable';


const FormInput = React.createClass({
  propTypes: {
    clickHandler: React.PropTypes.func.isRequired,
    tred: React.PropTypes.string.isRequired,
  },

  getInitialState() {
    return {
      bam: Settings.s3BAM,
      ref: Settings.ref,
    };
  },

  handleChange(e) {
    this.setState({ bam: e });
  },

  bamLink(text, bam) {
    return (
      <Button bsSize='large' bsStyle='link'
              onClick={ () => this.setState({ bam })
      }>{ text }</Button>
    );
  },

  _onOptionChange(ref) {
    this.setState({ ref });
  },

  render() {
    const buttonStyle = {
      marginBottom: '5px',
    };

    const Buttons = Object.keys(Treds).map((b) => {
      const active = (b === this.props.tred);
      return (
        <Button key={ b }
          onClick={ this.props.clickHandler.bind(null, this.state.bam, b, this.state.ref) }
          active={ active }
          bsSize='xsmall'
          style={ buttonStyle }
        >
          <div style={{ fontSize: '16px', fontWeight: 'bold' }}>{ b }
          </div> <div style={{ color: 'grey' }}>{ Treds[b].title }</div>
        </Button>
      );
    });

    return (
      <Form>
        <FormGroup>
          <Panel header={ <strong>BAM file</strong> }>
            <Typeahead
              type="text"
              ref='bam'
              bsSize="large"
              placeholder={ this.state.bam }
              options={ Settings.names }
              onInputChange={ this.handleChange }
            />
            <HelpBlock>
                BAM file can be on { this.bamLink('FTP', Settings.ftpBAM) } or {
                                     this.bamLink('S3', Settings.s3BAM) } on human reference <ButtonGroup>
                  <Button onClick={ this._onOptionChange.bind(this, 'hg38') }
                          active={ this.state.ref === 'hg38' }>
                    hg38
                  </Button>
                  <Button onClick={ this._onOptionChange.bind(this, 'hg19') }
                          active={ this.state.ref === 'hg19' }>
                    hg19
                  </Button>
                </ButtonGroup>
            </HelpBlock>
            <HelpBlock>
              <span style={{ fontWeight: 'bold' }}>Examples</span>:
                { this.bamLink('HD case', Settings.examples[0]) }
                { this.bamLink('DM1 case', Settings.examples[1]) }
                { this.bamLink('SCA17 case', Settings.examples[2]) }
                { this.bamLink('AR case', Settings.examples[3]) }
            </HelpBlock>
          </Panel>
        </FormGroup>

        <FormGroup>
          <Panel header={ <strong>STR locus</strong> }>
            <ButtonToolbar>
              { Buttons }
            </ButtonToolbar>
          </Panel>
        </FormGroup>
      </Form>
    );
  },
});

export default FormInput;
