import React from 'react';
import { ButtonGroup, ButtonToolbar, Button, FormControl, Form, FormGroup, HelpBlock, Panel } from 'react-bootstrap';
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
    this.setState({ bam: e.target.value });
  },

  _onOptionChange(ref) {
    this.setState({ ref: ref });
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
            <FormControl
              type="text"
              ref='bam'
              bsSize="large"
              value={ this.state.bam }
              placeholder="Enter sample BAM here"
              onChange={ this.handleChange }
            />
            <HelpBlock>
                BAM file could be on <Button bsSize='small' bsStyle='link'
                disabled
                onClick={ () =>
                  this.setState({ bam: Settings.httpBAM })
                }>HTTP</Button> or <Button bsSize='small'
                bsStyle='link'
                onClick={ () =>
                  this.setState({ bam: Settings.s3BAM })
                }>S3</Button> on human reference <ButtonGroup>
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
